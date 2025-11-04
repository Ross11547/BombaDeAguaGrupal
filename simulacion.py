import pygame, math
pygame.init()

ancho_ventana, alto_ventana = 1200, 700
ventana = pygame.display.set_mode((ancho_ventana, alto_ventana))
pygame.display.set_caption("Simulación Bomba de Agua – Diseño Básico")
reloj = pygame.time.Clock()
fuente_titulo = pygame.font.SysFont("consolas", 20, bold=True)
fuente_med    = pygame.font.SysFont("consolas", 16)
fuente_peq    = pygame.font.SysFont("consolas", 14)

color_fondo       = (245, 247, 250)
color_linea       = (30, 33, 38)
color_texto       = (32, 36, 40)
color_texto_sec   = (110, 110, 110)
color_agua_oscuro = (40, 95, 210)
color_agua_medio  = (60, 120, 240)
color_agua_claro  = (90, 160, 255)
color_tubo        = (30, 33, 38)
color_flotador    = (255, 210, 0)
color_bomba_cuerpo= (210, 210, 210)
color_bomba_borde = (32, 36, 40)
color_hormigon    = (220, 222, 226)
color_hormigon_r  = (170, 170, 175)

color_panel_sombra  = (0, 0, 0, 70)
color_panel_fondo   = (255, 255, 255)
color_panel_borde   = (206, 210, 220)
color_panel_texto   = (35, 38, 45)
color_panel_sutil   = (225, 229, 236)
color_panel_ok      = (17, 148, 70)
color_panel_alerta  = (206, 148, 18)
color_panel_peligro = (206, 55, 55)
color_acento        = (68, 134, 255)

color_barra_track = (234, 238, 244)
color_barra_fill  = (68, 134, 255)
color_barra_borde = (195, 202, 214)

color_boton_fondo = (40, 42, 48)
color_boton_borde = (210, 210, 210)
color_boton_texto = (240, 240, 240)
rect_boton_panel  = pygame.Rect(ancho_ventana - 170, alto_ventana - 54, 150, 38)

y_suelo = 320
ancho_camara_total = 410
alto_cisterna_px   = 220
x_cisterna         = 520

rect_cisterna = pygame.Rect(x_cisterna, y_suelo + 20, ancho_camara_total, alto_cisterna_px)
grosor_muro = 4
def rect_interno(r): return pygame.Rect(r.x + grosor_muro, r.y + grosor_muro, r.w - 2*grosor_muro, r.h - 2*grosor_muro)
rect_cisterna_int = rect_interno(rect_cisterna)

ancho_bomba, alto_bomba = 130, 55
rect_bomba = pygame.Rect(rect_cisterna.x + 20, y_suelo - alto_bomba - 12, ancho_bomba, alto_bomba)

rect_tanque_superior = pygame.Rect(170, 70, 280, 220)

panel_visible = True
rect_panel = pygame.Rect(ancho_ventana - 355, 00, 335, 300)

alto_cisterna_cm   = 200.0
alto_tanque_sup_cm = 200.0
px_por_cm_cis = rect_cisterna_int.h / alto_cisterna_cm
px_por_cm_sup = (rect_tanque_superior.h - 20) / alto_tanque_sup_cm
fondo_px_cis  = rect_cisterna_int.bottom
fondo_px_sup  = rect_tanque_superior.bottom - 10
def cm_a_y_cis(v): return int(fondo_px_cis - v * px_por_cm_cis)
def cm_a_y_sup(v): return int(fondo_px_sup - v * px_por_cm_sup)

nivel_cisterna_cm       = 140.0
nivel_tanque_sup_cm     = 30.0
altura_boca_manguera_cm = 120.0
bomba_on        = True
velocidad_bomba = 0.6
entrada_on      = False

caudal_entrada_lps_activo = 0.8
caudal_bomba_max_lps      = 1.5
consumo_tanque_sup_lps    = 0.3

area_cisterna_cm2   = 25000.0
area_tanque_sup_cm2 = 25000.0

distancia_suelo_segura_cm      = 50.0
distancia_superficie_segura_cm = 20.0
factor_tiempo_simulacion       = 8.0

def limitar(v, a, b):
    if v < a: return a
    if v > b: return b
    return v

def dibujar_texto(s, t, x, y, c=color_texto, f=fuente_med):
    s.blit(f.render(t, True, c), (x, y))

def agua_gradiente(s, x, y, w, h):
    if h <= 0: return
    pygame.draw.rect(s, color_agua_oscuro, (x, y, w, h))
    h2 = int(h*0.6)
    if h2>0: pygame.draw.rect(s, color_agua_medio, (x, y, w, h2))
    h3 = int(h*0.3)
    if h3>0: pygame.draw.rect(s, color_agua_claro, (x, y, w, h3))

def superficie(s, x0, x1, yb, t, col):
    pts, paso, x = [], 10, x0
    while x <= x1:
        off = math.sin((x*0.08) + t*3.0) * 2
        pts.append((x, yb + off)); x += paso
    if len(pts) >= 2: pygame.draw.lines(s, col, False, pts, 2)

def barra_h(s, x, y, w, h, p):
    pygame.draw.rect(s, color_barra_track, (x, y, w, h), border_radius=6)
    w2 = int(w * (p/100.0))
    if w2>0: pygame.draw.rect(s, color_barra_fill, (x, y, w2, h), border_radius=6)
    pygame.draw.rect(s, color_barra_borde, (x, y, w, h), 2, border_radius=6)

def sombra_rect(s, r, dx, dy, rad):
    surf = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
    pygame.draw.rect(surf, color_panel_sombra, pygame.Rect(0,0,r.w,r.h), border_radius=rad)
    s.blit(surf, (r.x + dx, r.y + dy))

def chip_estado(s, x, y, texto, activo):
    r = pygame.Rect(x, y, 120, 22)
    pygame.draw.rect(s, color_barra_track, r, border_radius=10)
    pygame.draw.rect(s, color_barra_borde, r, 1, border_radius=10)
    col = (20,160,90) if activo else (150,150,150)
    pygame.draw.circle(s, col, (r.x+12, r.y+11), 6)
    dibujar_texto(s, texto, r.x+26, r.y+3, color_panel_texto, fuente_peq)

def dibujar_tanque_superior(nivel, t):
    pygame.draw.rect(ventana, (240,240,240), rect_tanque_superior, border_radius=6)
    pygame.draw.rect(ventana, color_linea, rect_tanque_superior, 2, border_radius=6)
    m = 10; x = rect_tanque_superior.x + m; y = rect_tanque_superior.y + m
    w = rect_tanque_superior.w - 2*m; h = rect_tanque_superior.h - 2*m
    ys = cm_a_y_sup(nivel); yi = y + h
    if ys < yi:
        agua_gradiente(ventana, x, ys, w, yi-ys)
        superficie(ventana, x, x+w, ys, t, color_linea)
    dibujar_texto(ventana, "Tanque superior", rect_tanque_superior.x, rect_tanque_superior.y - 24, color_texto, fuente_peq)

def dibujar_cisterna(nivel, boca, t, entrada_activa):
    pygame.draw.rect(ventana, color_linea, rect_cisterna, grosor_muro, border_radius=4)

    y_sup = cm_a_y_cis(nivel)
    yi = rect_cisterna_int.bottom
    if y_sup < yi:
        agua_gradiente(ventana, rect_cisterna_int.x, y_sup, rect_cisterna_int.w, yi - y_sup)
        superficie(ventana, rect_cisterna_int.x, rect_cisterna_int.right, y_sup, t, color_linea)

    fx = rect_cisterna_int.x + int(rect_cisterna_int.w * 0.62)
    fy = y_sup - 8
    pygame.draw.circle(ventana, color_flotador, (fx, fy), 12)
    pygame.draw.circle(ventana, color_linea, (fx, fy), 12, 2)

    xt = rect_cisterna_int.x + int(rect_cisterna_int.w * 0.78)
    yt = rect_cisterna_int.y + 15
    yb = cm_a_y_cis(boca)
    pygame.draw.line(ventana, color_tubo, (xt, yt), (xt, yb), 6)
    pygame.draw.circle(ventana, color_tubo, (xt, yb), 8)

    y_tubo = rect_cisterna_int.y + 35
    x_izq  = rect_cisterna.x - 100
    x_codo = rect_cisterna_int.x + 15
    pygame.draw.line(ventana, color_tubo, (x_izq, y_tubo), (x_codo, y_tubo), 10)

    if entrada_activa:
        pygame.draw.line(ventana, color_acento, (x_izq+2, y_tubo), (x_codo-2, y_tubo), 5)
        pygame.draw.line(ventana, color_acento, (x_codo, y_tubo-2), (x_codo, y_tubo+50), 5)
    dibujar_texto(ventana, "Entrada de agua", x_izq, y_tubo - 20, color_texto_sec, fuente_peq)

def dibujar_losa_y_terreno():
    rect_losa = pygame.Rect(rect_cisterna.x, y_suelo, rect_cisterna.right - rect_cisterna.x, 14)
    pygame.draw.rect(ventana, color_hormigon, rect_losa)
    dx = rect_losa.x - 40
    while dx < rect_losa.right + 40:
        pygame.draw.line(ventana, color_hormigon_r, (dx, rect_losa.y+2), (dx-26, rect_losa.bottom-2), 1)
        dx += 12
    h = 30
    pygame.draw.rect(ventana, color_linea, (rect_cisterna.x + 20, y_suelo - h, 10, h))
    pygame.draw.rect(ventana, color_linea, (rect_cisterna.x + 20, y_suelo - h, 70, 10))
    pygame.draw.rect(ventana, color_linea, (rect_cisterna.right - 30, y_suelo - h, 10, h))
    pygame.draw.rect(ventana, color_linea, (rect_cisterna.right - 30, y_suelo - h, 70, 10))
    pygame.draw.line(ventana, (140,140,140), (100, y_suelo), (ancho_ventana-100, y_suelo), 3)

def dibujar_bomba_y_tuberias():
    x_toma = rect_cisterna_int.x + int(rect_cisterna_int.w * 0.78)
    y_linea_bomba = rect_bomba.centery
    pygame.draw.line(ventana, color_tubo, (x_toma, y_suelo), (x_toma, y_linea_bomba), 6)
    pygame.draw.line(ventana, color_tubo, (x_toma, y_linea_bomba), (rect_bomba.x, y_linea_bomba), 6)

    pygame.draw.rect(ventana, color_bomba_cuerpo, rect_bomba, border_radius=6)
    pygame.draw.rect(ventana, color_bomba_borde, rect_bomba, 2, border_radius=6)
    rect_cabezal = pygame.Rect(rect_bomba.right - 8, rect_bomba.centery - 15, 28, 30)
    pygame.draw.ellipse(ventana, color_bomba_cuerpo, rect_cabezal)
    pygame.draw.ellipse(ventana, color_bomba_borde, rect_cabezal, 2)
    rect_asa = pygame.Rect(rect_bomba.centerx - 15, rect_bomba.y - 10, 30, 10)
    pygame.draw.rect(ventana, color_bomba_cuerpo, rect_asa, border_radius=4)
    pygame.draw.rect(ventana, color_bomba_borde, rect_asa, 2, border_radius=4)
    dibujar_texto(ventana, "Bomba", rect_bomba.x + 8, rect_bomba.y - 24, color_texto, fuente_peq)

    x_salida = rect_cabezal.right
    y_salida = rect_bomba.centery
    y_altura_tanque = rect_tanque_superior.y + rect_tanque_superior.h // 2
    pygame.draw.line(ventana, color_tubo, (x_salida, y_salida), (x_salida, y_altura_tanque), 6)
    pygame.draw.line(ventana, color_tubo, (x_salida, y_altura_tanque), (rect_tanque_superior.x, y_altura_tanque), 6)
    pygame.draw.line(ventana, color_tubo, (rect_tanque_superior.x, y_altura_tanque),
                     (rect_tanque_superior.x, rect_tanque_superior.y + 24), 6)

def dibujar_controles():
    t = "[ESPACIO] bomba  [↑/↓] velocidad  [W/S] manguera  [I] entrada  [R] reset"
    y = rect_cisterna.bottom + 30
    w, h = fuente_peq.size(t)
    x = (ancho_ventana//2) - (w//2)
    px, py = 16, 10
    r = pygame.Rect(x-px, y-py, w+2*px, h+2*py)
    pygame.draw.rect(ventana, (235,238,245), r, border_radius=8)
    pygame.draw.rect(ventana, (180,184,192), r, 2, border_radius=8)
    dibujar_texto(ventana, t, x, y, (70,75,85), fuente_peq)

def dibujar_boton_panel(activo):
    pygame.draw.rect(ventana, color_boton_fondo, rect_boton_panel, border_radius=8)
    pygame.draw.rect(ventana, color_boton_borde, rect_boton_panel, 2, border_radius=8)
    etiqueta = "Ocultar panel" if activo else "Mostrar panel"
    dibujar_texto(ventana, etiqueta, rect_boton_panel.x + 18, rect_boton_panel.y + 10, color_boton_texto, fuente_med)

def dibujar_panel(q_bomba_lps, q_entrada_lps, alerta):
    if not panel_visible: return
    sombra_rect(ventana, rect_panel, 10, 10, 12)
    pygame.draw.rect(ventana, color_panel_fondo, rect_panel, border_radius=12)
    pygame.draw.rect(ventana, color_panel_borde, rect_panel, 7, border_radius=12)

    x = rect_panel.x + 20
    y = rect_panel.y + 20

    dibujar_texto(ventana, "Panel de simulación", x, y, color_panel_texto, fuente_titulo)
    pygame.draw.line(ventana, color_panel_sutil, (x, y+28), (rect_panel.right-16, y+28), 1)
    y += 36

    chip_estado(ventana, x, y, "Bomba", bomba_on)
    chip_estado(ventana, x+140, y, "Entrada", entrada_on)
    y += 30
    pygame.draw.line(ventana, color_panel_sutil, (x, y), (rect_panel.right-16, y), 1)
    y += 10

    dibujar_texto(ventana, "Velocidad", x, y, color_panel_texto, fuente_peq); y += 16
    barra_h(ventana, x, y, 210, 10, velocidad_bomba*100.0); y += 22

    pc = (nivel_cisterna_cm/alto_cisterna_cm)*100.0
    ps = (nivel_tanque_sup_cm/alto_tanque_sup_cm)*100.0

    dibujar_texto(ventana, "Cisterna", x, y, color_panel_texto, fuente_peq)
    dibujar_texto(ventana, f"{nivel_cisterna_cm:5.1f} cm", x+230, y, color_panel_texto, fuente_peq)
    y += 16; barra_h(ventana, x, y, 210, 10, pc); y += 22

    dibujar_texto(ventana, "Tanque sup", x, y, color_panel_texto, fuente_peq)
    dibujar_texto(ventana, f"{nivel_tanque_sup_cm:5.1f} cm", x+230, y, color_panel_texto, fuente_peq)
    y += 16; barra_h(ventana, x, y, 210, 10, ps); y += 14
    pygame.draw.line(ventana, color_panel_sutil, (x, y+12), (rect_panel.right-16, y+12), 1); y += 24

    dibujar_texto(ventana, f"Q bomba:   {q_bomba_lps*60:5.1f} L/min", x, y, color_panel_texto, fuente_peq); y += 18
    dibujar_texto(ventana, f"Q entrada: {q_entrada_lps*60:5.1f} L/min", x, y, color_panel_texto, fuente_peq); y += 12

    if alerta == "":
        dibujar_texto(ventana, "OK (sin alertas)", x, y+6, color_panel_ok, fuente_peq)
    else:
        col = color_panel_alerta
        if "PELIGRO" in alerta or "CRITICO" in alerta: col = color_panel_peligro
        dibujar_texto(ventana, alerta, x, y+6, col, fuente_peq)

ejecutando, tiempo_total = True, 0.0
while ejecutando:
    dt = reloj.tick(60)/1000.0
    tiempo_total += dt
    dt_fisica = dt * factor_tiempo_simulacion

    for e in pygame.event.get():
        if e.type == pygame.QUIT: ejecutando = False
        elif e.type == pygame.KEYDOWN:
            if e.key == pygame.K_SPACE: bomba_on = not bomba_on
            elif e.key == pygame.K_i:    entrada_on = not entrada_on
            elif e.key == pygame.K_r:
                nivel_cisterna_cm, nivel_tanque_sup_cm = 140.0, 30.0
                altura_boca_manguera_cm = 120.0
                bomba_on, velocidad_bomba, entrada_on = True, 0.6, False
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if rect_boton_panel.collidepoint(e.pos): panel_visible = not panel_visible

    teclas = pygame.key.get_pressed()
    if teclas[pygame.K_UP]:   velocidad_bomba += 0.7*dt
    if teclas[pygame.K_DOWN]: velocidad_bomba -= 0.7*dt
    if teclas[pygame.K_w]:    altura_boca_manguera_cm += 45.0*dt
    if teclas[pygame.K_s]:    altura_boca_manguera_cm -= 45.0*dt

    li = distancia_suelo_segura_cm
    ls = max(li, nivel_cisterna_cm - distancia_superficie_segura_cm)
    altura_boca_manguera_cm = limitar(altura_boca_manguera_cm, li, ls)
    velocidad_bomba = limitar(velocidad_bomba, 0.0, 1.0)

    entrada_lps = caudal_entrada_lps_activo if entrada_on else 0.0
    boca_sumergida  = nivel_cisterna_cm > (altura_boca_manguera_cm + 2.0)
    factor_sumergida= 1.0 if boca_sumergida else 0.05
    elevacion_base_tanque_cm = 250.0
    altura_entrega_cm = elevacion_base_tanque_cm + nivel_tanque_sup_cm - altura_boca_manguera_cm
    if altura_entrega_cm < 0: altura_entrega_cm = 0.0
    factor_presion = 1.0 - (altura_entrega_cm/400.0)
    factor_presion = limitar(factor_presion, 0.3, 1.0)

    caudal_bomba_lps = (velocidad_bomba if bomba_on else 0.0) * caudal_bomba_max_lps * factor_sumergida * factor_presion

    delta_vol_cis_cm3 = (entrada_lps - caudal_bomba_lps) * 1000.0 * dt_fisica
    nivel_cisterna_cm = limitar(nivel_cisterna_cm + delta_vol_cis_cm3/area_cisterna_cm2, 0.0, alto_cisterna_cm)

    delta_vol_sup_cm3 = (caudal_bomba_lps - consumo_tanque_sup_lps) * 1000.0 * dt_fisica
    nivel_tanque_sup_cm = limitar(nivel_tanque_sup_cm + delta_vol_sup_cm3/area_tanque_sup_cm2, 0.0, alto_tanque_sup_cm)

    alerta = ""
    if not boca_sumergida and bomba_on: alerta = "PELIGRO: succión de aire"
    elif altura_boca_manguera_cm <= distancia_suelo_segura_cm + 1: alerta = "Cuidado: muy cerca del fondo"
    elif nivel_cisterna_cm <= distancia_suelo_segura_cm + 5: alerta = "CRITICO: cisterna casi vacía"

    ventana.fill(color_fondo)
    dibujar_tanque_superior(nivel_tanque_sup_cm, tiempo_total)
    dibujar_bomba_y_tuberias()
    dibujar_cisterna(nivel_cisterna_cm, altura_boca_manguera_cm, tiempo_total, entrada_on)
    dibujar_losa_y_terreno()
    dibujar_controles()
    dibujar_boton_panel(panel_visible)
    dibujar_panel(caudal_bomba_lps, entrada_lps, alerta)
    pygame.display.flip()

pygame.quit()
