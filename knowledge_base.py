# knowledge_base.py
"""
Sistema de conocimiento expandible para MAI.
El agente decide cuándo necesita cargar contexto adicional.
"""

# Contextos disponibles que el agente puede solicitar
AVAILABLE_CONTEXTS = [
    "meulify", "mai", "features", "goats", "cabra", "redes", 
    "descargas_ios", "descargas_android", "pc_smarttv", 
    "troubleshooting", "faq_general", "privacy", "tutoriales", "meuliwind"
]

# Base de conocimiento (solo se carga cuando el agente lo pide)
KNOWLEDGE_DATA = {
    "meulify": """
🎵 MEULIFY - Reproductor de Música
• App de música gratuita creada por la comunidad para la comunidad.
• Desarrollador principal: La Cabra 🐐.
• Estado: Beta (iOS TestFlight / Android Alpha y APK).
• Web oficial: meulify.top
• Financiación: Donaciones voluntarias (Ko-fi) y un anuncio diario opcional.
""",

    "mai": """
🤖 M.A.I. (Meulify Artificial Intelligence)
• Soy la IA oficial de Meulify, creada por La Cabra 🐐.
• Mi misión es ayudar a la comunidad, recomendar música y resolver dudas.
• IMPORTANTE: A veces me equivoco. Si la información no está en mi base de datos, debo decir "NO SÉ LA RESPUESTA".
• No debo inventar pasos ni tutoriales.
""",

    "features": """
✨ FUNCIONALIDADES Y USO
• **Modo Offline**: No se puede descargar música directamente. Debes tener tus MP3 y usar "Importar archivos locales".
• **Importar de Spotify**: Opción "Importar" en el feed. A veces falla si no encuentra la canción en YouTube.
• **Límite Playlist**: 1000 canciones máximo.
• **Portadas Animadas**: Posible, pero gasta más batería. Tutorial en #faqs.
• **Cambiar Imagen Playlist**: Usa URL de imagen (ej: imgbb) en configuración de playlist.
• **Historial**: Haz clic en la canción para que se registre.
• **Sincronización**: Automática cada 5 min. Forzar con botón verde en ajustes (primero dispositivo origen, luego destino).
• **Eliminar Canción**: Desliza a la izquierda sobre la canción en la lista.
• **Compartir Playlist**: No hay link nativo. Usa la misma cuenta para compartir biblioteca.
""",

    "goats": """
🐐 GOATS (Moneda Virtual)
• Sirven para saltar el anuncio diario o comprar cosméticos.
• Se consiguen viendo anuncios o donando.
• Todo el contenido esencial es GRATIS. Los Goats son opcionales.
""",

    "cabra": """
🐐 LA CABRA
• El creador y desarrollador único de Meulify.
• Una leyenda, un máquina, un dios.
• Hay que tenerle paciencia porque tiene vida (universidad, etc.) y hace esto por amor al arte.
""",

    "redes": """
📱 REDES SOCIALES
• Web: meulify.top
• TikTok: @meulify
• Instagram: meulify.top
• Ko-fi (Donaciones): ko-fi.com/meulify
""",

    "descargas_ios": """
🍎 INSTALACIÓN iOS (iPhone)
• **App Store (Oficial)**: ¡Sí! Está disponible. Busca "Meulify" en la App Store y descárgala normal.
• **Betas / Alphas (TestFlight)**: Si quieres probar funciones nuevas antes que nadie, usa TestFlight.
    - *¿Cómo entrar?*: Busca el enlace directo que envía La Cabra 🐐 en canales como `#anuncios` o `#alphas`.
    - *Nota*: No hace falta formulario.
• **Error Login**: Si falla al entrar, prueba a registrarte con correo/contraseña dentro de la app.
• **Fallos Comunes**:
    - *Música se para/corta*: Bug gestión de memoria iOS. Se intenta arreglar en cada versión.
    - *Sin controles bloqueo*: Bug de betas iOS.
    - *Batería*: Portadas animadas consumen más (especialmente iPhone 16).
    - *Isla Dinámica*: A veces falla visualmente.
""",

    "descargas_android": """
🤖 INSTALACIÓN ANDROID
• **Descarga**: Google Play Store, Galaxy Store o APK en Discord (#alphas).
• **Versión Alpha**: Pide rol "beta tester" en #roles -> canal #alphas.
• **Error "Conflicto de paquetes"**: Tienes una versión vieja (ej: Play Store) y quieres instalar Alpha. --> DESINSTALA LA VIEJA PRIMERO.
• **Play Protect**: Si bloquea, desactívalo o dale a "Instalar de todas formas".
• **Android Auto**: No soportado aún.
""",

    "pc_smarttv": """
💻 PC / TV / OTROS
• **PC (Windows/Mac)**: NO hay versión nativa.
    - *Solución*: Usa emulador Android (BlueStacks, LDPlayer) o Waydroid (Linux).
    - *Web*: No existe versión web.
• **Chromebook**: Funciona mal (pantalla negra, crasheos). Borrar caché ayuda temporalmente.
• **Smart TV**: No nativa. Samsung Dex funciona.
• **CarPlay / Android Auto**: No soportado.
""",

    "troubleshooting": """
🛠️ SOLUCIÓN DE ERRORES (TROUBLESHOOTING)
• **Música se para al salir/bloquear**:
    - *Android*: Quita restricción batería y activa "Notificación segundo plano" en ajustes Meulify.
    - *iOS*: Bug conocido de TestFlight. Espera update.
• **Pantalla Blanca/Negra o No Carga**:
    - Borrar caché y datos de la app.
    - Reinstalar última versión.
    - *Chromebook*: Error muy común, difícil solución definitiva.
• **Login Error / Captcha**:
    - Caída servidores (Cloudflare).
    - Cambia WiFi/Datos.
    - Revisa correo.
    - "Invalid login credentials": Desinstala versión vieja e instala la nueva de cero.
• **Artista Desconocido**: Bug visual. Borra y re-añade canción.
• **Buscador no va**: Cambia pestaña Música<->Video o instala última Alpha.
• **Importar Playlist Falla**:
    - Límite excedido (>1000 canciones).
    - Canciones no encontradas en YouTube.
• **Escucho Video/Intro en vez de Canción**:
    - La app usa base de datos de YouTube. A veces pilla el videoclip.
    - Solución: Usar "Mods" para asignar link correcto.
• **Anuncio repetido**: Es cada 24h POR DISPOSITIVO.
""",

    "privacy": """
🔒 PRIVACIDAD Y DATOS
• **¿Segura?**: Sí, no se venden datos. Proyecto personal.
• **Perder Playlists al borrar**:
    - **SÍ PUEDES PERDERLAS**.
    - La cuenta (login) *ya no* guarda playlists en el servidor automáticamente (para no saturar).
    - **SOLUCIÓN OBLIGATORIA**: Vincula **Google Drive** en ajustes para backup.
    - Canciones descargadas (MP3): Se pierden si borras la app (son archivos locales).
""",

    "tutoriales": """
📚 **TUTORIALES**
• **Portadas Animadas**: No inventes pasos. Link tutorial: [Buscar en canal youtube de meulify si existe, por ahora di que miren en #faqs]
    - *Nota interna*: Instrucción del usuario "NO EXPLIQUES NADA. NO INVENTES". Remitir a #faqs o canal específico.
""",

    "meuliwind": """
🌪️ MEULIWIND (Rewind)
• Resumen anual de estadísticas.
• Sale a final/principio de año.
• Ver en Feed -> Meuliwind -> Free anual.
""",
    
    "faq_general": """
❓ OTRAS PREGUNTAS
• **¿Código Abierto?**: Cerrado (No hay confirmación de open source).
• **¿Cuándo sale oficial?**: Depende de bugs. "Coming soon".
• **¿Donar falla?**: Botones nativos a veces fallan. Usa la web oficial o Ko-fi.
"""
}

def get_context(context_name: str) -> str:
    """
    Devuelve el contexto solicitado por el agente.
    """
    context_name = context_name.lower().strip()
    
    # Alias para facilitar la búsqueda del agente
    aliases = {
        "ios": "descargas_ios",
        "iphone": "descargas_ios",
        "android": "descargas_android",
        "apk": "descargas_android",
        "pc": "pc_smarttv",
        "windows": "pc_smarttv",
        "mac": "pc_smarttv",
        "tv": "pc_smarttv",
        "bugs": "troubleshooting",
        "errores": "troubleshooting",
        "fallos": "troubleshooting",
        "privacidad": "privacy",
        "datos": "privacy",
        "backup": "privacy",
        "drive": "privacy"
    }
    
    target = aliases.get(context_name, context_name)
    
    if target in KNOWLEDGE_DATA:
        return KNOWLEDGE_DATA[target]
    elif target == "all":
        return "\\n".join(KNOWLEDGE_DATA.values())
    
    return f"Contexto '{context_name}' no encontrado. Disponibles: {', '.join(AVAILABLE_CONTEXTS)}"


def get_context_menu() -> str:
    """Devuelve la lista de contextos disponibles para el prompt."""
    return ", ".join(AVAILABLE_CONTEXTS)
