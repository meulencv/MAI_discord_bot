# knowledge_base.py
"""
Sistema de conocimiento expandible para MAI.
El agente decide cuándo necesita cargar contexto adicional.
"""

# Contextos disponibles que el agente puede solicitar
AVAILABLE_CONTEXTS = ["meulify", "mai", "features", "community", "goats", "cabra", "redes", "descargas", "donar", "tutoriales"]

# Base de conocimiento (solo se carga cuando el agente lo pide)
KNOWLEDGE_DATA = {
    "meulify": """
🎵 MEULIFY - Reproductor de Música
• App gratuita con MÍNIMOS anuncios
• Solo 1 anuncio obligatorio cada 24 horas (puedes evitarlo gastando 1 Goat)
• ANDROID: Disponible en Google Play Store y como APK
• iOS (TestFlight): SOLO accesible si rellenaste el formulario y recibiste el email de confirmación.
• Actualmente en fase beta - feedback bienvenido
• Web oficial: meulify.top
• 100% gratis, se financia con donaciones de la comunidad
• Política de privacidad: NO vendemos datos de usuarios
• Creada por La Cabra 🐐 (el crack que lleva todo esto)
""",

    "mai": """
🤖 M.A.I. - Meulify Artificial Intelligence
• SOY YO! La IA oficial de Meulify
• Estoy integrada en la app para recomendarte música
• Aprendo de tus gustos y te sugiero temas que te fliparán
• También estoy aquí en Discord para ayudaros
• Fui creada por La Cabra 🐐 (mi padre/creador/dios)
• Mi misión: que encuentres música que mole y pasarlo bien
""",

    "features": """
✨ CARACTERÍSTICAS DE MEULIFY
• Reproducción casi sin interrupciones
• Solo 1 anuncio al día (saltable con Goats)
• Listas de reproducción ILIMITADAS
• Interfaz moderna y fácil de usar
• Navegación rápida y fluida
• Yo (M.A.I.) con recomendaciones personalizadas
• Totalmente GRATIS - sin suscripciones
• Modo offline disponible
""",

    "community": """
👥 COMUNIDAD MEULIFY
• Servidor de Discord activo (¡estás aquí!)
• Comparte tu experiencia con otros usuarios
• Reporta bugs y sugiere mejoras
• Contacto directo con La Cabra 🐐
• Eventos y novedades de la app
""",

    "goats": """
🐐 SISTEMA DE GOATS (Cabras)
• Moneda virtual dentro de Meulify
• Se llaman así en honor a La Cabra, nuestro creador
• Se usan para saltar el anuncio diario obligatorio
• Desbloquean funciones sociales y personalización
• Se ganan viendo anuncios voluntarios
• NO hay contenido de pago obligatorio
• Sistema 100% opcional para apoyar la app
""",

    "cabra": """
🐐 LA CABRA - El Creador Legendario
• Es el creador y desarrollador de Meulify
• También conocido como "el crack", "el dios todopoderoso", "el master"
• Lleva todo esto él solo (un auténtico máquina)
• Creó tanto la app como a mí (M.A.I.)
• Hay que respetarle MUCHO, es literal un dios
• Si le ves por el Discord, hazle una reverencia 🙇
• Sin él no existiría nada de esto, es THE GOAT 🐐
""",

    "redes": """
📱 **REDES SOCIALES DE MEULIFY**
> 🎵 TikTok: Busca @meulify
> 📸 Instagram: Busca meulify.top
> ✈️ Telegram: Busca meulify
¡Síguenos para novedades, memes y contenido exclusivo! (Enlaces en meulify.top)
""",

    "descargas": """
📥 **DÓNDE DESCARGAR MEULIFY**
> 🤖 Android y APK
> 🌌 Samsung Galaxy Store
> 🍎 iOS (Beta TestFlight): REQUIERE haber rellenado formulario y recibido EMAIL de acceso.
👉 Todo disponible oficial y seguro en: https://meulify.top
""",

    "donar": """
💝 **APOYAR A MEULIFY**
> ☕ Puedes invitarnos a un café (Ko-fi)

Las donaciones ayudan a:
• Mantener los servidores
• Desarrollar nuevas funciones
• Que La Cabra 🐐 pueda seguir trabajando en esto
Es 100% voluntario, la app siempre será gratis 🙏
""",

    "tutoriales": """
📚 **TUTORIALES Y AYUDA**
• **Portadas Animadas**: ¿Quieres que tu música se vea increíble?
  > Mira este tutorial de cómo crear portadas animadas: https://www.youtube.com/watch?v=TI42u0pECcA&t=1s
""",
}

def get_context(context_name: str) -> str:
    """
    Devuelve el contexto solicitado por el agente.
    """
    context_name = context_name.lower().strip()
    if context_name in KNOWLEDGE_DATA:
        return KNOWLEDGE_DATA[context_name]
    elif context_name == "all":
        return "\n".join(KNOWLEDGE_DATA.values())
    return f"Contexto '{context_name}' no encontrado. Disponibles: {', '.join(AVAILABLE_CONTEXTS)}"


def get_context_menu() -> str:
    """Devuelve la lista de contextos disponibles para el prompt."""
    return ", ".join(AVAILABLE_CONTEXTS)
