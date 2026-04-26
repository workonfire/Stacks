import gettext
from pathlib import Path

GETTEXT_DOMAIN = "stacks"

LOCALE_DIR = Path(__file__).resolve().parent.parent / "po"


def setup_translations() -> gettext.NullTranslations:
    translation = gettext.translation(
        GETTEXT_DOMAIN,
        localedir=LOCALE_DIR,
        fallback=True,
    )
    translation.install()
    return translation


_translation = setup_translations()
_ = _translation.gettext