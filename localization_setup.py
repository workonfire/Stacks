import gettext
import locale
from pathlib import Path

APP_ID = "stacks"

LOCALE_DIR = Path(__file__).resolve().parent.parent / "po"


def setup_translations() -> gettext.NullTranslations:
    language, _encoding = locale.getlocale()
    languages = [language] if language else None

    translation = gettext.translation(
        APP_ID,
        localedir=LOCALE_DIR,
        languages=languages,
        fallback=True,
    )
    translation.install()
    return translation


_translation = setup_translations()
_ = _translation.gettext
