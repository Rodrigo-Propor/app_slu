#!/usr/bin/env python3
# coding: utf-8
"""
Script to convert GDI files from estacao total to .txt format with coordinates
"""
import re
import math
import pandas as pd
import numpy as np
from pathlib import Path

KNOWN_POINTS = {
    'B1':  {'N': 7797920.066, 'E': 603204.240, 'Z': 872.612},
    'B3':  {'N': 7797702.453, 'E': 603701.764, 'Z': 917.476},
    'B2':  {'N': 7797415.706, 'E': 602706.344, 'Z': 933.347},
    'M1':  {'N': 7797895.410, 'E': 603166.188, 'Z': 866.415},
    'M2':  {'N': 7798224.951, 'E': 603387.740, 'Z': 878.446},
    'M12': {'N': 7797419.817, 'E': 603537.402, 'Z': 896.209},
    'M6':  {'N': 7797414.178, 'E': 602705.809, 'Z': 932.224},
    'M7':  {'N': 7797228.400, 'E': 602698.415, 'Z': 935.806},
    'P6':  {'N': 7798121.2425, 'E': 603330.3861, 'Z': 871.682},
    'P5':  {'N': 7797970.8793, 'E': 603237.2298, 'Z': 870.163},
    'P4':  {'N': 7797929.5485, 'E': 603211.6355, 'Z': 871.095},
    'P3':  {'N': 7797787.0342, 'E': 603121.5513, 'Z': 884.940},
    'P2':  {'N': 7797727.7990, 'E': 603081.9594, 'Z': 896.213},
    'P1':  {'N': 7797725.0599, 'E': 603037.4223, 'Z': 900.518},
    'P9':  {'N': 7798230.8492, 'E': 603410.5553, 'Z': 879.479},
    'P9B': {'N': 7798066.9662, 'E': 603659.2369, 'Z': 929.346},
}

def dms_to_decimal(dms_str):
    """Convert DMS string to decimal degrees"""
    try:
        clean_str = re.sub(r'[^\d]', '', dms_str)
        if len(clean_str) < 5: 
            return 0.0
        
        sec = float(clean_str[-2:])
        min_val = float(clean_str[-4:-2])
        deg = float(clean_str[:-4]) if len(clean_str) > 4 else 0.0
        
        return deg + (min_val / 60.0) + (sec / 3600.0)
    except:
        return 0.0

def get_azimuth(n1, e1, n2, e2):
    """Calculate azimuth from point 1 to point 2"""
    delta_n = n2 - n1
    delta_e = e2 - e1
    az_rad = math.atan2(delta_e, delta_n)
    az_deg = math.degrees(az_rad)
    if az_deg < 0:
        az_deg += 360.0
    return az_deg

def parse_gd2i_file(content, known_points, calib_theta=None):
    """Parse GDI raw file and extract points with calculated coordinates"""
    
    regex_station = r"(?i)_\+'([A-Z0-9]+)_\(E_\)([\d\.]+)_+\+([A-Z0-9]+)_"
    regex_reading = r"(?i)\?([\+\-]?\d+)m(\d+)([\+\-]?\d+)d"
    regex_point = r"(?i)_\*([A-Za-z0-9\.]+)[,_]*,?([\d\.]+)_+\+([A-Za-z0-9]+)_\s*\?([\+\-]?\d+)m(\d+)([\+\-]?\d+)d"

    points_calculated = []
    
    current_stn = None
    current_hi = 0.0
    azimuth_correction = 0.0
    
    stn_match = re.search(regex_station, content)
    if stn_match:
        stn_id = stn_match.group(1)
        try:
            current_hi = float(stn_match.group(2))
        except Exception:
            current_hi = 0.0
        bs_id = stn_match.group(3)
        current_stn = stn_id
        
        if calib_theta is not None:
            azimuth_correction = float(calib_theta) % 360.0
        else:
            read_match = re.search(regex_reading, content)
            if stn_id in known_points and bs_id in known_points:
                stn_n = known_points[stn_id]['N']
                stn_e = known_points[stn_id]['E']
                bs_n = known_points[bs_id]['N']
                bs_e = known_points[bs_id]['E']
                true_azimuth = get_azimuth(stn_n, stn_e, bs_n, bs_e)
                measured_angle = dms_to_decimal(read_match.group(2)) if read_match else 0.0
                azimuth_correction = true_azimuth - measured_angle
                print(f"  Station: {stn_id} -> Backsight: {bs_id} | Correction: {azimuth_correction:.4f} deg")
            elif stn_id in known_points:
                azimuth_correction = 0.0
    else:
        if "B1" in known_points:
            current_stn = "B1"
            current_hi = 0.0
            azimuth_correction = 0.0
    
    for pt_match in re.finditer(regex_point, content):
        if current_stn not in known_points:
            continue
        
        code = pt_match.group(1)
        try:
            ht = float(pt_match.group(2))
        except Exception:
            ht = 0.0
        
        pt_id = pt_match.group(3)
        s_dist_raw = float(pt_match.group(4))
        slope_dist = s_dist_raw / 1000.0
        ha_raw = pt_match.group(5)
        va_raw = pt_match.group(6)
        
        h_angle = dms_to_decimal(ha_raw)
        v_angle = dms_to_decimal(va_raw)
        azimuth = h_angle + azimuth_correction
        
        az_rad = math.radians(azimuth)
        vert_rad = math.radians(v_angle)
        
        horiz_dist = slope_dist * math.cos(vert_rad)
        diff_level = slope_dist * math.sin(vert_rad)
        
        n0 = known_points[current_stn]['N']
        e0 = known_points[current_stn]['E']
        z0 = known_points[current_stn]['Z']
        
        nf = n0 + horiz_dist * math.cos(az_rad)
        ef = e0 + horiz_dist * math.sin(az_rad)
        zf = z0 + current_hi + diff_level - ht
        
        points_calculated.append({
            'Ponto': pt_id,
            'Descricao': code,
            'Este': round(ef, 4),
            'Norte': round(nf, 4),
            'Cota': round(zf, 4),
        })

    return pd.DataFrame(points_calculated)

def converter_arquivos_perfil():
    """Convert files from perfil folder and save as .txt"""
    raiz = Path(__file__).parent
    pasta_perfil = raiz / "perfil"
    saida = raiz / "conversoes_final"
    saida.mkdir(exist_ok=True)
    
    if not pasta_perfil.exists():
        print("ERROR: Folder not found:", pasta_perfil)
        return
    
    print("\nProcessing files from folder:", pasta_perfil)
    print("-" * 60)
    
    arquivos = [f for f in pasta_perfil.iterdir() if f.is_file()]
    
    if not arquivos:
        print("ERROR: No files found in perfil folder!")
        return
    
    processados = 0
    
    for arquivo in sorted(arquivos):
        try:
            print("\nFile:", arquivo.name)
            conteudo = arquivo.read_bytes().decode("latin-1", errors="ignore")
        except Exception as e:
            print(f"  ERROR reading file: {e}")
            continue
        
        df = parse_gd2i_file(conteudo, KNOWN_POINTS)
        
        if df.empty:
            print("  WARNING: No points extracted")
            continue
        
        destino_txt = saida / (arquivo.stem + ".txt")
        try:
            with destino_txt.open("w", encoding="utf-8") as f:
                for _, row in df.iterrows():
                    ponto = str(row['Ponto']).strip()
                    descricao = str(row['Descricao']).strip()
                    este = float(row['Este'])
                    norte = float(row['Norte'])
                    cota = float(row['Cota'])
                    f.write(f"{ponto},{descricao},{este:.4f},{norte:.4f},{cota:.4f}\n")
            
            print(f"  SUCCESS: {destino_txt.name}")
            print(f"  Extracted: {len(df)} points")
            processados += 1
            
        except Exception as e:
            print(f"  ERROR saving file: {e}")
    
    print("\n" + "-" * 60)
    print(f"\nProcessing completed: {processados} file(s) converted")
    print(f"Output folder: {saida.resolve()}\n")

if __name__ == "__main__":
    print("=" * 60)
    print("GDI to TXT Converter")
    print("Total Station GDI File to Text File")
    print("=" * 60)
    converter_arquivos_perfil()
