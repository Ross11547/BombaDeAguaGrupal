import pygame, math, wave, struct, os
from pid_controller import PID, PIDGains

#Sonido de la alarma
def crear_beep_wav(path:str, freq=880, dur_s=0.30, vol=0.6, samplerate=44100):
    nframes = int(dur_s * samplerate)
    amp = int(32767 * max(0.0, min(vol, 1.0)))
    with wave.open(path, "w") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(samplerate)
        for i in range(nframes):
            t = i / samplerate
            wf.writeframes(struct.pack("<h", int(amp * math.sin(2*math.pi*freq*t))))

# pygame
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
ancho_ventana, alto_ventana = 1200, 700
ventana = pygame.display.set_mode((ancho_ventana, alto_ventana))
pygame.display.set_caption("Simulación Bomba de Agua + PID")
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

#Panel de simulacion
panel_visible = True
rect_panel = pygame.Rect(ancho_ventana -400, 0, 380, 430) #Cambie los valores, valores anteriores 355, 00, 335, 300

#Panel del PID
pid_panel_visible = True
rect_pid_panel=pygame.Rect(20,20,360,240)

# Botones
btn_w,btn_h,btn_gap=150,38,10
rect_boton_panel   = pygame.Rect(ancho_ventana-170, alto_ventana-54, btn_w, btn_h)        # Mostrar/Ocultar
rect_btn_vac_cis   = pygame.Rect(rect_boton_panel.x-(btn_w+btn_gap),   alto_ventana-54, btn_w, btn_h)  # Vaciar cisterna
rect_btn_vac_sup   = pygame.Rect(rect_boton_panel.x-(btn_w+btn_gap)*2, alto_ventana-54, btn_w, btn_h)  # Vaciar tanque
rect_btn_pid_panel = pygame.Rect(rect_boton_panel.x-(btn_w+btn_gap)*3, alto_ventana-54, btn_w, btn_h)  # Mostrar Panel PID


alto_cisterna_cm   = 200
alto_tanque_sup_cm = 200
px_por_cm_cis = (rect_cisterna.h-2*grosor_muro)/alto_cisterna_cm
px_por_cm_sup = (rect_tanque_superior.h - 20) / alto_tanque_sup_cm
fondo_px_cis  = rect_cisterna.bottom-grosor_muro
fondo_px_sup  = rect_tanque_superior.bottom - 10
def cm_a_y_cis(v): return int(fondo_px_cis - v * px_por_cm_cis)
def cm_a_y_sup(v): return int(fondo_px_sup - v * px_por_cm_sup)

nivel_cisterna_cm       = 140
nivel_tanque_sup_cm     = 30
altura_boca_manguera_cm = 120
bomba_on        = True
velocidad_bomba = 0.6
entrada_on      = False

caudal_entrada_lps_activo = 0.8
caudal_bomba_max_lps      = 1.5
consumo_tanque_sup_lps    = 0.3

area_cisterna_cm2   = 25000
area_tanque_sup_cm2 = 25000

distancia_suelo_segura_cm      = 50
distancia_superficie_segura_cm = 20
factor_tiempo_simulacion       = 8

#Alarmas
umbral_sin_agua_cm=1.0                                       # Umbral para considerar sin agua
proteccion_seco_on=True
alarma_mute=False; alarma_vol=0.9; parpadeo_t=0.0

#PID
pid_enabled=False
pid_target_cm=120.0
pid=PID(PIDGains(kp=0.08, ki=0.02, kd=0.04), umin=0.0, umax=1.0, tau=0.08)  # Controlador PID

#Auto-llenado PID de la cisterna
auto_llenado_activo=False
entrada_forzada_por_pid=False #Se refiere a la entrada de agua
umbral_auto_on  = 50.0 # El nivel del agua es <50 se considera vacio y entra al auto llenado
umbral_auto_off = 60.0 # El nivel del agua es >60 se considera suficiente agua y termina al auto llenado
umbral_auto_on  = 50.0 # El nivel del agua es <50 se considera vacio y entra al auto llenado
umbral_auto_off = 60.0 # El nivel del agua es >50 se considera suficiente agua y termina al auto llenado

allow_pid_auto_start = True #Cuando sale del autollenado enciende la bomba para que llene el tanque porq ya hay agua en la cisterna

# Audio
tmp_beep=os.path.join(os.path.dirname(__file__), "_beep_temp.wav")
try:
    crear_beep_wav(tmp_beep, 900, 0.35, 1.0)
    beep_sound=pygame.mixer.Sound(tmp_beep); beep_sound.set_volume(alarma_vol)
    alarma_channel=pygame.mixer.Channel(0)
except Exception:
    beep_sound=None; alarma_channel=None

#UI
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

#Lo modifique para que se ajuste automáticamente al texto y evitar que las etiquetas se salgan o se superpongan.
def chip_estado_surface(surf, x, y, texto, activo, font=fuente_peq):
    pad_x=12; h=22
    tw,th = font.size(texto)
    w = max(100, 26 + tw + 8)
    r=pygame.Rect(x,y,w,h)
    pygame.draw.rect(surf, (234,238,244), r, border_radius=10)
    pygame.draw.rect(surf, (195,202,214), r, 1, border_radius=10)
    col=(20,160,90) if activo else (150,150,150)
    pygame.draw.circle(surf, col, (r.x+12, r.y+h//2), 6)
    surf.blit(font.render(texto, True, color_panel_texto), (r.x+26, r.y+(h-th)//2))
    return r.right

# Ajusta automáticamente el texto en múltiples líneas para que no se salga del panel.
def draw_wrapped_text(surf, text, x, y, max_w, color=color_panel_texto, font=fuente_peq, line_gap=4):
    if not text:
        return y
    words = text.split(' ')
    line = ""
    for w in words:
        t = (line + (" " if line else "") + w)
        if font.size(t)[0] <= max_w:
            line = t
        else:
            surf.blit(font.render(line, True, color), (x, y))
            y += font.get_linesize() + line_gap
            line = w
    if line:
        surf.blit(font.render(line, True, color), (x, y))
        y += font.get_linesize() + line_gap
    return y

#Para las etiquetas del panel
def draw_label_value(surf, x, y, w, label, value, font=fuente_peq, color=color_panel_texto):
    lw, lh = font.size(label)
    vw, _  = font.size(value)
    surf.blit(font.render(label, True, color), (x, y))
    surf.blit(font.render(value, True, color), (x + w - vw, y))
    return y + font.get_linesize() + 2

def make_panel_surface(rect, title_text):
    sombra_rect(ventana, rect, 10, 10, 12)
    pygame.draw.rect(ventana, color_panel_fondo, rect, border_radius=12)
    pygame.draw.rect(ventana, color_panel_borde, rect, 7, border_radius=12)

    surf = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
    padding = 16
    inner = pygame.Rect(padding, padding, rect.w - 2*padding, rect.h - 2*padding)
    surf.set_clip(inner)

    title_y = padding
    t_surf = fuente_titulo.render(title_text, True, color_panel_texto)
    surf.blit(t_surf, (padding, title_y))

    sep_y = title_y + t_surf.get_height() + 8
    pygame.draw.line(surf, color_panel_sutil, (padding, sep_y), (rect.w - padding, sep_y), 1)

    return surf, padding, sep_y + 12, inner

def blit_panel_surface(surf, rect):
    ventana.blit(surf, rect.topleft)

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
    t = "[ESPACIO] bomba  [↑/↓] velocidad  [W/S] manguera  [I] entrada  [R] reset  [M] mute [V/T/X] vaciar [Q] PID [F] Panel PID"
    y = rect_cisterna.bottom + 30
    w, h = fuente_peq.size(t)
    x = (ancho_ventana//2) - (w//2)
    px, py = 16, 10
    r = pygame.Rect(x-px, y-py, w+2*px, h+2*py)
    pygame.draw.rect(ventana, (235,238,245), r, border_radius=8)
    pygame.draw.rect(ventana, (180,184,192), r, 2, border_radius=8)
    dibujar_texto(ventana, t, x, y, (70,75,85), fuente_peq)

#boton de mostrar el panel
def dibujar_boton_panel(activo):
    pygame.draw.rect(ventana, color_boton_fondo, rect_boton_panel, border_radius=8)
    pygame.draw.rect(ventana, color_boton_borde, rect_boton_panel, 2, border_radius=8)
    etiqueta = "Ocultar panel" if activo else "Mostrar panel"
    dibujar_texto(ventana, etiqueta, rect_boton_panel.x + 18, rect_boton_panel.y + 10, color_boton_texto, fuente_med)

#para todos los demas botones
def dibujar_boton(r,txt):
    pygame.draw.rect(ventana, color_boton_fondo, r, border_radius=8)
    pygame.draw.rect(ventana, color_boton_borde, r,2, border_radius=8)
    w,h=fuente_med.size(txt)
    dibujar_texto(ventana, txt, r.x+(r.w-w)//2, r.y+(r.h-h)//2, color_boton_texto, fuente_med)

#Paneles
def dibujar_panel_general(q_bomba_lps, q_entrada_lps, alerta_txt):
    if not panel_visible: return
    surf, pad, y, inner = make_panel_surface(rect_panel, "Panel de simulación")
    x = pad; w = inner.w

    right = chip_estado_surface(surf, x, y, "Bomba", bomba_on)
    right = chip_estado_surface(surf, right + 10, y, "Entrada", entrada_on)
    y += 28
    right = chip_estado_surface(surf, x, y, "Protección", proteccion_seco_on)
    right = chip_estado_surface(surf, right + 10, y, "Alarma", not alarma_mute)
    y += 28
    right = chip_estado_surface(surf, x, y, "PID", pid_enabled)
    right = chip_estado_surface(surf, right + 10, y, "Panel PID", pid_panel_visible)
    y += 28
    y += 32

    y = draw_label_value(surf, x, y, w, "Velocidad bomba", f"{velocidad_bomba*100:5.1f}%")
    barra_h(surf, x, y, w, 10, velocidad_bomba*100.0); y += 18

    y = draw_label_value(surf, x, y, w, "Cisterna", f"{nivel_cisterna_cm:5.1f} cm")
    barra_h(surf, x, y, w, 10, (nivel_cisterna_cm/alto_cisterna_cm)*100.0); y += 18
    y = draw_label_value(surf, x, y, w, "Tanque sup", f"{nivel_tanque_sup_cm:5.1f} cm")
    barra_h(surf, x, y, w, 10, (nivel_tanque_sup_cm/alto_tanque_sup_cm)*100.0); y += 10

    y += 8
    y = draw_label_value(surf, x, y, w, "Q bomba",   f"{q_bomba_lps*60:5.1f} L/min")
    y = draw_label_value(surf, x, y, w, "Q entrada", f"{q_entrada_lps*60:5.1f} L/min")

    y += 6
    if alerta_txt:
        y = draw_wrapped_text(surf, alerta_txt, x, y, w, color_panel_peligro, fuente_peq, line_gap=2)
    else:
        y = draw_wrapped_text(surf, "OK (sin alertas)", x, y, w, color_panel_ok, fuente_peq, line_gap=2)

    blit_panel_surface(surf, rect_panel)

def dibujar_panel_pid():
    if not pid_panel_visible: return
    surf, pad, y, inner = make_panel_surface(rect_pid_panel, "Panel PID")
    x = pad; w = inner.w

    chip_estado_surface(surf, x, y, "PID", pid_enabled); y += 28

    if pid_enabled:
        y = draw_label_value(surf, x, y, w, "Setpoint (SP)", f"{pid_target_cm:5.1f} cm")
        y = draw_label_value(surf, x, y, w, "Proceso (PV)",  f"{nivel_tanque_sup_cm:5.1f} cm")
        e = pid_target_cm - nivel_tanque_sup_cm
        y = draw_label_value(surf, x, y, w, "Error (SP-PV)", f"{e:5.1f} cm")

        y += 4
        y = draw_wrapped_text(surf,
                              f"Kp:{pid.kp:.3f}    Ki:{pid.ki:.3f}    Kd:{pid.kd:.3f}",
                              x, y, w, color_panel_texto, fuente_peq, line_gap=2)
        y = draw_label_value(surf, x, y, w, "Salida u", f"{velocidad_bomba*100:5.1f} %")
    else:
        y = draw_wrapped_text(surf, "PID desactivado (pulsa Q).", x, y, w, color_texto_sec, fuente_peq)

    blit_panel_surface(surf, rect_pid_panel)

def dibujar_boton_panel(activo):
    dibujar_boton(rect_boton_panel,"Ocultar panel" if activo else "Mostrar panel")

def dibujar_banner_alerta(texto,t):
    fase=(math.sin(t*8.0)+1.0)/2.0; alpha=int(80+120*fase)
    surf=pygame.Surface((ancho_ventana,38),pygame.SRCALPHA)
    pygame.draw.rect(surf,(255,40,40,alpha),surf.get_rect()); ventana.blit(surf,(0,0))
    dibujar_texto(ventana,texto,16,10,(255,255,255),fuente_med)

def dibujar_banner_pid(texto,t,offset_y=40):
    fase=(math.sin(t*6.0)+1.0)/2.0; alpha=int(60+110*fase)
    surf=pygame.Surface((ancho_ventana,30),pygame.SRCALPHA)
    pygame.draw.rect(surf,(68,134,255,alpha),surf.get_rect()); ventana.blit(surf,(0,offset_y))
    dibujar_texto(ventana,texto,16,offset_y+6,(255,255,255),fuente_peq)


ejecutando=True; tiempo_total=0.0
while ejecutando:
    dt = reloj.tick(60)/1000.0
    tiempo_total += dt
    parpadeo_t+=dt
    dt_fisica = dt * factor_tiempo_simulacion

    for e in pygame.event.get():
        if e.type==pygame.QUIT: ejecutando=False
        elif e.type==pygame.KEYDOWN:
            if e.key==pygame.K_SPACE: bomba_on=not bomba_on
            elif e.key==pygame.K_i: entrada_on=not entrada_on
            elif e.key==pygame.K_p: proteccion_seco_on=not proteccion_seco_on
            elif e.key==pygame.K_m: alarma_mute=not alarma_mute
            elif e.key in (pygame.K_PLUS, pygame.K_EQUALS):
                alarma_vol=limitar(alarma_vol+0.1,0,1)
                if 'beep_sound' in locals() and beep_sound: beep_sound.set_volume(alarma_vol)
            elif e.key==pygame.K_MINUS:
                alarma_vol=limitar(alarma_vol-0.1,0,1)
                if 'beep_sound' in locals() and beep_sound: beep_sound.set_volume(alarma_vol)
            elif e.key==pygame.K_v: nivel_cisterna_cm=0.0
            elif e.key==pygame.K_t: nivel_tanque_sup_cm=0.0
            elif e.key==pygame.K_x: nivel_cisterna_cm=0.0; nivel_tanque_sup_cm=0.0
            elif e.key==pygame.K_q: pid_enabled=not pid_enabled; pid.reset()
            elif e.key==pygame.K_LEFTBRACKET:  pid_target_cm=limitar(pid_target_cm-5.0,0,alto_tanque_sup_cm)
            elif e.key==pygame.K_RIGHTBRACKET: pid_target_cm=limitar(pid_target_cm+5.0,0,alto_tanque_sup_cm)
            elif e.key==pygame.K_1: pid.set_gains(kp=pid.kp-0.01)
            elif e.key==pygame.K_2: pid.set_gains(kp=pid.kp+0.01)
            elif e.key==pygame.K_3: pid.set_gains(ki=pid.ki-0.005)
            elif e.key==pygame.K_4: pid.set_gains(ki=pid.ki+0.005)
            elif e.key==pygame.K_5: pid.set_gains(kd=pid.kd-0.01)
            elif e.key==pygame.K_6: pid.set_gains(kd=pid.kd+0.01)
            elif e.key==pygame.K_f: pid_panel_visible=not pid_panel_visible
            elif e.key==pygame.K_a: allow_pid_auto_start = not allow_pid_auto_start
            elif e.key==pygame.K_r:
                nivel_cisterna_cm, nivel_tanque_sup_cm = 140.0, 30.0
                altura_boca_manguera_cm=120.0
                bomba_on=True; velocidad_bomba=0.6; entrada_on=False
                pid_enabled=False; pid_panel_visible=True; panel_visible=True
                auto_llenado_activo=False; entrada_forzada_por_pid=False
                allow_pid_auto_start=True
                pid.reset()
        elif e.type==pygame.MOUSEBUTTONDOWN and e.button==1:
            if rect_boton_panel.collidepoint(e.pos): panel_visible=not panel_visible
            elif rect_btn_vac_cis.collidepoint(e.pos): nivel_cisterna_cm=0.0
            elif rect_btn_vac_sup.collidepoint(e.pos): nivel_tanque_sup_cm=0.0
            elif rect_btn_pid_panel.collidepoint(e.pos): pid_panel_visible=not pid_panel_visible

    teclas = pygame.key.get_pressed()
    if not pid_enabled:
        if teclas[pygame.K_UP]: velocidad_bomba+=0.7*dt
        if teclas[pygame.K_DOWN]: velocidad_bomba-=0.7*dt
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

    # Estado agua
    sin_agua_cis = (nivel_cisterna_cm <= umbral_sin_agua_cm)   #cisterna vacía
    sin_agua_sup = (nivel_tanque_sup_cm <= umbral_sin_agua_cm)  #tanque vacio

    #Auto-llenado + verificación de bomba
    if pid_enabled:
        if sin_agua_cis and not auto_llenado_activo: # Disparo de auto-llenado
            auto_llenado_activo = True
            entrada_forzada_por_pid = True

        if auto_llenado_activo:
            entrada_on = True # Abre entrada del agua
            velocidad_bomba = 0.0 # Evita bombear porque no hay agua en la cisterna
            if nivel_cisterna_cm >= umbral_auto_off: # Condición de salida
                auto_llenado_activo = False
                if entrada_forzada_por_pid:
                    entrada_on = False # Cierra entrada del agua si la abrió el PID
                    entrada_forzada_por_pid = False
                if allow_pid_auto_start and (nivel_cisterna_cm > altura_boca_manguera_cm + 2.0):
                    bomba_on = True # Enciende bomba porq ya hay agua en la cisterna
        else:
            if not bomba_on:
                if allow_pid_auto_start and (nivel_cisterna_cm > altura_boca_manguera_cm + 2.0):
                    bomba_on = True
            if bomba_on:
                u_pid = pid.step(pid_target_cm, nivel_tanque_sup_cm, dt_fisica)
                velocidad_bomba = limitar(u_pid, 0.0, 1.0)

    caudal_bomba_lps = (velocidad_bomba if bomba_on else 0.0) * caudal_bomba_max_lps * factor_sumergida * factor_presion

    delta_vol_cis_cm3 = (entrada_lps - caudal_bomba_lps) * 1000.0 * dt_fisica
    nivel_cisterna_cm = limitar(nivel_cisterna_cm + delta_vol_cis_cm3/area_cisterna_cm2, 0.0, alto_cisterna_cm)

    delta_vol_sup_cm3 = (caudal_bomba_lps - consumo_tanque_sup_lps) * 1000.0 * dt_fisica
    nivel_tanque_sup_cm = limitar(nivel_tanque_sup_cm + delta_vol_sup_cm3/area_tanque_sup_cm2, 0.0, alto_tanque_sup_cm)

    # Alertas
    alerta_txt = ""
    if sin_agua_cis:
        alerta_txt = "CRÍTICO: Cisterna sin agua"
    elif sin_agua_sup:
        alerta_txt = "Alerta: Tanque superior sin agua"
    if (not boca_sumergida) and bomba_on:
        if alerta_txt == "":
            alerta_txt = "PELIGRO: succión de aire"
        if proteccion_seco_on:
            bomba_on = False

    # Sonido de alarma
    quiere_alarma = (alerta_txt != "") and (not alarma_mute)
    if beep_sound and alarma_channel:
        if quiere_alarma:
            if not alarma_channel.get_busy():
                alarma_channel.play(beep_sound, loops=-1)
        else:
            if alarma_channel.get_busy():
                alarma_channel.stop()

    # Mensaje PID para banners
    pid_msg = ""
    if pid_enabled:
        if auto_llenado_activo:
            pid_msg = "PID corrigiendo: auto-llenando cisterna"
        elif not bomba_on:
            pid_msg = "PID en espera: bomba apagada"
        elif sin_agua_sup:
            pid_msg = "PID corrigiendo: recuperando tanque superior"

    ventana.fill(color_fondo)
    dibujar_tanque_superior(nivel_tanque_sup_cm, tiempo_total)
    dibujar_bomba_y_tuberias()
    dibujar_cisterna(nivel_cisterna_cm, altura_boca_manguera_cm, tiempo_total, entrada_on)
    dibujar_losa_y_terreno()
    dibujar_controles()

    dibujar_boton(rect_btn_pid_panel, "Panel PID")
    dibujar_boton(rect_btn_vac_sup, "Vaciar tanque")
    dibujar_boton(rect_btn_vac_cis, "Vaciar cisterna")
    dibujar_boton_panel(panel_visible)
    dibujar_panel_general(caudal_bomba_lps, entrada_lps, alerta_txt)
    dibujar_panel_pid()

    # Banners de alerta e información PID
    if alerta_txt:
        dibujar_banner_alerta(alerta_txt, parpadeo_t)
        if pid_msg:
            dibujar_banner_pid(pid_msg, parpadeo_t, offset_y=40)
    else:
        if pid_msg:
            dibujar_banner_pid(pid_msg, parpadeo_t, offset_y=10)

    pygame.display.flip()

try:
    if alarma_channel and alarma_channel.get_busy(): alarma_channel.stop()
except: pass
pygame.quit()
try:
    if os.path.exists(tmp_beep): os.remove(tmp_beep)
except: pass

