import re
import math
import pandas as pd
import numpy as np
from pathlib import Path

# --- 1. BANCO DE DADOS DE COORDENADAS (SAD69) ---
# Extraído do arquivo "COORDENADAS - MARCOS SLU (1).txt"
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
    """Converte string 'GGGMMSS' para graus decimais."""
    try:
        clean_str = re.sub(r'[^\d]', '', dms_str)
        if len(clean_str) < 5: return 0.0
        
        # Formato esperado do arquivo raw parece variar, assumindo dddmmss
        # Se a string for muito longa ou curta, ajustamos
        sec = float(clean_str[-2:])
        min = float(clean_str[-4:-2])
        deg = float(clean_str[:-4]) if len(clean_str) > 4 else 0.0
        
        return deg + (min / 60.0) + (sec / 3600.0)
    except:
        return 0.0

def get_azimuth(n1, e1, n2, e2):
    """Calcula o azimute geográfico de P1 para P2 em graus (0-360)."""
    delta_n = n2 - n1
    delta_e = e2 - e1
    az_rad = math.atan2(delta_e, delta_n)
    az_deg = math.degrees(az_rad)
    if az_deg < 0:
        az_deg += 360.0
    return az_deg

def parse_gd2i_file(content, known_points, calib_theta=None):
    """
    Processa o arquivo bruto.
    Lógica:
    1. Procura linhas de Estação (_'ST_...) para definir onde estamos e a Ré.
    2. Calcula a correção de ângulo baseada nas coordenadas conhecidas.
    3. Processa pontos de irradiação (*CODE_...).
    """
    
    # Regex ajustados para o formato específico dos arquivos PERFILM / PERFIL9M
    # Captura Estação, Alt Instrumento (HI) e Ré
    regex_station = r"(?i)_\+'([A-Z0-9]+)_\(E_\)([\d\.]+)_+\+([A-Z0-9]+)_"
    
    # Captura leitura da Ré (que vem logo após a definição da estação na mesma linha ou próxima)
    # Exemplo: ...+M2_ ?+00355391m0885515+... (Dist, AngHoriz, AngVert)
    regex_reading = r"(?i)\?([\+\-]?\d+)m(\d+)([\+\-]?\d+)d"
    
    # Captura Pontos Irradiados
    # Ex: _*R_,1.600_+P9_ ?+... (Code, AltAlvo, NomePonto, Leitura...)
    regex_point = r"(?i)_\*([A-Za-z0-9\.]+)[,_]*,?([\d\.]+)_+\+([A-Za-z0-9]+)_\s*\?([\+\-]?\d+)m(\d+)([\+\-]?\d+)d"

    points_calculated = []
    
    # Divide o arquivo em "blocos" lógicos baseados nos separadores comuns
    # O arquivo é meio bagunçado, vamos tentar iterar encontrando padrões
    
    current_stn = None
    current_hi = 0.0
    azimuth_correction = 0.0
    
    # Primeiro, vamos normalizar o texto para facilitar regex (remover quebras de linha no meio de dados)
    # Mas cuidado para não juntar registros diferentes.
    # Vamos processar por "tokens" de registros que parecem começar com _' ou _*
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
                print(f"Estação {stn_id} -> Ré {bs_id}")
                print(f"Azimute Calc: {true_azimuth:.4f}, Lido: {measured_angle:.4f}, Correção: {azimuth_correction:.4f}")
            elif stn_id in known_points:
                azimuth_correction = 0.0
            else:
                pass
    else:
        if "M8" in known_points:
            current_stn = "M8"
            current_hi = 0.0
            azimuth_correction = float(calib_theta) % 360.0 if calib_theta is not None else 0.0
        elif "B1" in known_points:
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
            'Estacao': current_stn,
            'Ponto': pt_id,
            'Descricao': code,
            'Norte': round(nf, 3),
            'Este': round(ef, 3),
            'Cota': round(zf, 3),
            'Dist_Horiz': round(horiz_dist, 3),
            'Azimute': round(azimuth % 360, 4)
        })
        if pt_id not in known_points:
            known_points[pt_id] = {'N': nf, 'E': ef, 'Z': zf}

    return pd.DataFrame(points_calculated)

def parse_em_txt_coords():
    base = Path(__file__).parent / "txt"
    dados = {}
    for p in base.glob("EM*M.TXT"):
        try:
            texto = p.read_text(encoding="latin-1", errors="ignore")
        except Exception:
            continue
        for linha in texto.splitlines():
            partes = [s.strip() for s in linha.split(",")]
            if len(partes) < 5:
                continue
            rotulo = partes[1]
            try:
                e = float(partes[2])
                n = float(partes[3])
                z = float(partes[4])
            except Exception:
                continue
            if rotulo not in dados:
                dados[rotulo] = {"E": [], "N": [], "Z": []}
            dados[rotulo]["E"].append(e)
            dados[rotulo]["N"].append(n)
            dados[rotulo]["Z"].append(z)
    med = {}
    for k, v in dados.items():
        med[k] = {
            "E": float(np.nanmedian(v["E"])) if v["E"] else np.nan,
            "N": float(np.nanmedian(v["N"])) if v["N"] else np.nan,
            "Z": float(np.nanmedian(v["Z"])) if v["Z"] else np.nan,
        }
    return med

def parse_inclinometro_txt_coords():
    base = Path(__file__).parent / "txt"
    coords = {}
    for p in list(base.glob("ICL*.TXT")) + list(base.glob("PEM*.TXT")):
        try:
            texto = p.read_text(encoding="latin-1", errors="ignore")
        except Exception:
            continue
        for linha in texto.splitlines():
            partes = [s.strip() for s in linha.split(",")]
            if len(partes) < 4:
                continue
            rotulo = partes[0]
            if not rotulo or not rotulo.upper().startswith("I"):
                continue
            try:
                e = float(partes[1])
                n = float(partes[2])
                z = float(partes[3])
            except Exception:
                continue
            coords[rotulo] = {"E": e, "N": n, "Z": z}
    return coords

def parse_em_observations(content):
    regex_station = r"(?i)_'([A-Za-z0-9]+)_\(E_\)([\d\.]+)_+\+([A-Za-z0-9]+)_"
    regex_reading = r"(?i)\?([\+\-]?\d+)m(\d+)([\+\-]?\d+)d"
    regex_point = r"(?i)_\*([A-Za-z0-9\.]+)[,_]*,?([\d\.]+)_+\+([A-Za-z0-9]+)_\s*\?([\+\-]?\d+)m(\d+)([\+\-]?\d+)d"
    tokens = re.split(r'(?=_\'|_\*)', content)
    obs = []
    current_stn = None
    current_hi = 0.0
    for token in tokens:
        if not token.strip():
            continue
        stn_match = re.search(regex_station, token)
        if stn_match:
            current_stn = stn_match.group(1)
            try:
                current_hi = float(stn_match.group(2))
            except Exception:
                current_hi = 0.0
        pt_match = re.search(regex_point, token)
        if pt_match and current_stn == "M8":
            code = pt_match.group(1)
            try:
                ht = float(pt_match.group(2))
            except Exception:
                ht = 0.0
            s_dist_raw = float(pt_match.group(4))
            slope_dist = s_dist_raw / 1000.0
            ha_raw = pt_match.group(5)
            va_raw = pt_match.group(6)
            h_angle = dms_to_decimal(ha_raw)
            v_angle = dms_to_decimal(va_raw)
            vert_rad = math.radians(v_angle)
            horiz_dist = slope_dist * math.cos(vert_rad)
            diff_level = slope_dist * math.sin(vert_rad)
            obs.append({
                "label": code,
                "d": horiz_dist,
                "a": h_angle,
                "hi": current_hi,
                "ht": ht,
                "dl": diff_level,
            })
    return obs

def compute_m8_from_raw(content, label_coords):
    obs = parse_em_observations(content)
    pares = []
    for o in obs:
        if o["label"] in label_coords:
            c = label_coords[o["label"]]
            if not np.isnan(c["E"]) and not np.isnan(c["N"]):
                pares.append({"E": c["E"], "N": c["N"], "Z": c.get("Z", np.nan), "d": o["d"], "a": o["a"], "hi": o["hi"], "ht": o["ht"], "dl": o["dl"]})
    if len(pares) < 3:
        return None
    def erro(theta_deg):
        th = math.radians(theta_deg)
        e0s = [p["E"] - p["d"] * math.sin(th + math.radians(p["a"])) for p in pares]
        n0s = [p["N"] - p["d"] * math.cos(th + math.radians(p["a"])) for p in pares]
        e0 = float(np.nanmedian(e0s))
        n0 = float(np.nanmedian(n0s))
        res = 0.0
        for p in pares:
            pe = e0 + p["d"] * math.sin(th + math.radians(p["a"]))
            pn = n0 + p["d"] * math.cos(th + math.radians(p["a"]))
            de = pe - p["E"]
            dn = pn - p["N"]
            res += de*de + dn*dn
        return res, e0, n0
    best = (float("inf"), 0.0, 0.0, 0.0)
    for th in np.linspace(0.0, 360.0, 721):
        r, e0, n0 = erro(th)
        if r < best[0]:
            best = (r, th, e0, n0)
    th0 = best[1]
    step = 0.05
    for th in np.arange(max(0.0, th0-1.0), min(360.0, th0+1.0)+step, step):
        r, e0, n0 = erro(th)
        if r < best[0]:
            best = (r, th, e0, n0)
    e0 = best[2]
    n0 = best[3]
    z0s = []
    for p in pares:
        if not np.isnan(p["Z"]):
            z0s.append(p["Z"] - p["hi"] - p["dl"] + p["ht"])
    z0 = float(np.nanmedian(z0s)) if z0s else np.nan
    return {"E": e0, "N": n0, "Z": z0, "theta": best[1]}

def ler_arquivos_raiz_e_converter():
    raiz = Path(__file__).parent
    saida = raiz / "conversoes_final"
    saida.mkdir(exist_ok=True)
    for p in saida.glob("*.csv"):
        try:
            p.unlink()
        except Exception:
            pass
    for p in saida.glob("*.txt"):
        try:
            p.unlink()
        except Exception:
            pass
    candidatos = []
    for p in raiz.iterdir():
        if not p.is_file():
            continue
        nome = p.name.upper()
        if p.suffix.lower() in ("", ".txt"):
            if not nome.endswith(".PY") and not nome.endswith(".MD"):
                candidatos.append(p)
        elif nome.startswith(("EM", "IC", "LV", "PA", "PE")):
            candidatos.append(p)
    for arquivo in candidatos:
        try:
            conteudo = arquivo.read_bytes().decode("latin-1", errors="ignore")
        except Exception:
            continue
        stn = None
        m = re.search(r"_+'([A-Z0-9]+)_\(E_\)", conteudo)
        if m:
            stn = m.group(1)
        calib_theta = None
        if stn == "M8" and "M8" not in KNOWN_POINTS:
            labels = {}
            candidato_txt = arquivo.parent / (arquivo.name + "M.TXT")
            if candidato_txt.exists():
                try:
                    texto = candidato_txt.read_text(encoding="latin-1", errors="ignore")
                    for linha in texto.splitlines():
                        partes = [s.strip() for s in linha.split(",")]
                        if len(partes) >= 5:
                            try:
                                desc = partes[1]
                                e = float(partes[2])
                                n = float(partes[3])
                                z = float(partes[4])
                                labels[desc] = {"E": e, "N": n, "Z": z}
                            except Exception:
                                pass
                except Exception:
                    pass
            else:
                labels = parse_em_txt_coords()
            m8 = compute_m8_from_raw(conteudo, labels)
            if m8:
                KNOWN_POINTS["M8"] = {"N": m8["N"], "E": m8["E"], "Z": m8["Z"]}
                calib_theta = m8.get("theta")
        df = parse_gd2i_file(conteudo, KNOWN_POINTS, calib_theta=calib_theta)
        ref_txt = arquivo.parent / (arquivo.name + "M.TXT")
        if ref_txt.exists() and not df.empty:
            try:
                texto = ref_txt.read_text(encoding="latin-1", errors="ignore")
                mapa = {}
                for ln in texto.splitlines():
                    ps = [s.strip() for s in ln.split(",")]
                    if len(ps) >= 5:
                        try:
                            desc = ps[1]
                            e = float(ps[2])
                            n = float(ps[3])
                            z = float(ps[4])
                            mapa[desc] = (e, n, z)
                        except Exception:
                            pass
                if "Descricao" in df.columns and {"Norte","Este","Cota"}.issubset(df.columns):
                    for idx in df.index:
                        d = str(df.at[idx, "Descricao"]).strip()
                        if d in mapa:
                            e, n, z = mapa[d]
                            df.at[idx, "Este"] = e
                            df.at[idx, "Norte"] = n
                            df.at[idx, "Cota"] = z
            except Exception:
                pass
        if df.empty:
            continue
        destino = saida / (arquivo.stem + ".csv")
        try:
            df.to_csv(destino, index=False, sep=";")
            print(f"Convertido: {arquivo.name} -> {destino} ({len(df)} linhas)")
        except Exception as e:
            print(f"Erro ao salvar {destino.name}: {str(e)}")

def processar_pasta_perfil():
    """Processa arquivos da pasta 'perfil' e gera .txt diretamente"""
    raiz = Path(__file__).parent
    pasta_perfil = raiz / "perfil"
    saida = raiz / "conversoes_final"
    saida.mkdir(exist_ok=True)
    
    if not pasta_perfil.exists():
        print(f"Pasta '{pasta_perfil}' não encontrada!")
        return
    
    print(f"\nProcessando arquivos da pasta: {pasta_perfil}\n")
    
    # Procura arquivos .unknown e sem extensão
    arquivos = list(pasta_perfil.glob("*")) + list(pasta_perfil.glob("*.unknown"))
    arquivos = [a for a in arquivos if a.is_file()]
    
    for arquivo in arquivos:
        try:
            conteudo = arquivo.read_bytes().decode("latin-1", errors="ignore")
        except Exception as e:
            print(f"Erro ao ler {arquivo.name}: {e}")
            continue
        
        # Detectar estação
        stn = None
        m = re.search(r"_+'([A-Z0-9]+)_\(E_\)", conteudo)
        if m:
            stn = m.group(1)
        
        calib_theta = None
        if stn == "M8" and "M8" not in KNOWN_POINTS:
            labels = parse_em_txt_coords()
            m8 = compute_m8_from_raw(conteudo, labels)
            if m8:
                KNOWN_POINTS["M8"] = {"N": m8["N"], "E": m8["E"], "Z": m8["Z"]}
                calib_theta = m8.get("theta")
                print(f"M8 calculado: N={m8['N']:.3f}, E={m8['E']:.3f}, Z={m8['Z']:.3f}")
        
        # Processar pontos
        df = parse_gd2i_file(conteudo, KNOWN_POINTS, calib_theta=calib_theta)
        
        if df.empty:
            print(f"⚠️  {arquivo.name}: Nenhum ponto extraído")
            continue
        
        # Salvar como .txt
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
            print(f"✅ {arquivo.name} -> {destino_txt.name} ({len(df)} pontos)")
        except Exception as e:
            print(f"❌ Erro ao salvar {destino_txt.name}: {e}")

def consolidar_pontos():
    """Consolida todos os .txt em um arquivo único"""
    raiz = Path(__file__).parent
    pasta = raiz / "conversoes_final"
    
    if not pasta.exists():
        return
    
    # Lê todos os CSVs e converte para .txt
    arquivos = list(pasta.glob("*.csv"))
    dfs = []
    
    for arq in arquivos:
        try:
            df = pd.read_csv(arq, sep=";")
        except Exception:
            continue
        cols = [c for c in df.columns]
        if set(["Ponto","Norte","Este","Cota","Descricao"]).issubset(cols):
            df2 = df[["Ponto","Norte","Este","Cota","Descricao"]].copy()
            df2.columns = ["ponto","norte","este","cota","descricao"]
            incl = parse_inclinometro_txt_coords()
            if incl:
                mask_i = df2["descricao"].astype(str).str.upper().str.startswith("I")
                for idx in df2[mask_i].index:
                    code = str(df2.at[idx, "descricao"])  
                    if code in incl:
                        df2.at[idx, "este"] = incl[code]["E"]
                        df2.at[idx, "norte"] = incl[code]["N"]
                        df2.at[idx, "cota"] = incl[code]["Z"]
            dfs.append(df2)
    
    if dfs:
        final = pd.concat(dfs, ignore_index=True)
        destino_unico = pasta / "pontos_consolidados.csv"
        final.to_csv(destino_unico, index=False, sep=";")
        destino_txt = pasta / "pontos_consolidados.txt"
        with destino_txt.open("w", encoding="utf-8") as f:
            for _, r in final.iterrows():
                f.write(f"{str(r['ponto']).strip()},{str(r['descricao']).strip()},{float(r['este']):.4f},{float(r['norte']):.4f},{float(r['cota']):.4f}\n")
        print(f"\n✅ Consolidado: {destino_txt} ({len(final)} pontos)")


if __name__ == "__main__":
    print("=" * 60)
    print("CONVERSOR DE COORDENADAS - ESTAÇÃO TOTAL GDI")
    print("=" * 60)
    
    # Processa arquivos da raiz
    print("\n[1/3] Processando arquivos da raiz...")
    ler_arquivos_raiz_e_converter()
    
    # Processa pasta perfil
    print("\n[2/3] Processando arquivos da pasta 'perfil'...")
    processar_pasta_perfil()
    
    # Consolida
    print("\n[3/3] Consolidando pontos...")
    consolidar_pontos()
    
    print("\n" + "=" * 60)
    print("✅ Processamento concluído!")
    print("=" * 60)