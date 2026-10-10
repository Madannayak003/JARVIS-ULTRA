"""
JARVIS PRO
Developer Analyzer

Framework -> Language Rules
"""

from brain.developer.enums import Framework, Language


FRAMEWORK_LANGUAGE_RULES = {

    Framework.FLASK: Language.PYTHON,

    Framework.DJANGO: Language.PYTHON,

    Framework.FASTAPI: Language.PYTHON,

    Framework.REACT: Language.JAVASCRIPT,

    Framework.VUE: Language.JAVASCRIPT,

    Framework.EXPRESS: Language.JAVASCRIPT,

    Framework.NEXTJS: Language.TYPESCRIPT,

}