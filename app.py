from __future__ import annotations

import base64
from pathlib import Path
from urllib.parse import quote

import streamlit as st
import streamlit.components.v1 as components


BASE_DIR = Path(__file__).parent
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
QR_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".svg"}
YOUTUBE_VIDEO_ID = "qG4M5eF0WjU"
QR_PLACEHOLDER = BASE_DIR / "qrcode_placeholder.svg"
WHATSAPP_PHONE = "2389752640"
DEFAULT_WHATSAPP_MESSAGE = (
    "Olá, tenho interesse no Chevy Equinox. "
    "Gostaria de receber mais informações."
)
# Video position relative to the photo gallery: 1 before it, 2 or higher after it.
GALLERY_VIDEO_POSITION = 2
PHOTO_QUERY_PARAM = "foto"


def is_qr_file(path: Path) -> bool:
    normalized_name = path.stem.lower().replace("-", "").replace("_", "")
    return (
        "qrcode" in normalized_name
        or normalized_name.startswith("qr")
        or normalized_name.endswith("contact")
    )


def discover_assets(extensions: set[str]) -> list[Path]:
    return sorted(
        path
        for path in BASE_DIR.iterdir()
        if path.is_file()
        and path.suffix.lower() in extensions
        and not path.stem.endswith("_web")
        and not is_qr_file(path)
    )


def discover_qr_code() -> Path:
    qr_files = sorted(
        path
        for path in BASE_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in QR_EXTENSIONS and is_qr_file(path)
    )
    return qr_files[0] if qr_files else QR_PLACEHOLDER


def encode_file(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def file_data_uri(path: Path) -> str:
    extension = path.suffix.lower()
    mime_type = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".svg": "image/svg+xml",
    }.get(extension, "application/octet-stream")
    return f"data:{mime_type};base64,{encode_file(path)}"


def whatsapp_url(message: str = DEFAULT_WHATSAPP_MESSAGE) -> str:
    encoded_message = quote(message.strip() or DEFAULT_WHATSAPP_MESSAGE, safe="")
    return f"https://wa.me/{WHATSAPP_PHONE}?text={encoded_message}"


def current_gallery_index(image_count: int) -> int:
    raw_index = st.query_params.get(PHOTO_QUERY_PARAM, "1")
    try:
        index = int(raw_index) - 1
    except (TypeError, ValueError):
        index = 0

    return index % image_count


def render_photo_gallery(images: list[Path]) -> None:
    if not images:
        st.markdown(
            '<div class="empty-state">Adicione fotos na pasta para ativar a galeria.</div>',
            unsafe_allow_html=True,
        )
        return

    image_count = len(images)
    current_index = current_gallery_index(image_count)

    slides = []
    dots = []
    for index, image_path in enumerate(images):
        active_class = " is-active" if index == current_index else ""
        image_src = file_data_uri(image_path)
        slides.append(
            f'<figure class="manual-gallery-slide{active_class}" data-gallery-slide="{index}">'
            f'<img src="{image_src}" alt="Chevrolet Equinox 2019 foto {index + 1}" />'
            "</figure>"
        )
        dots.append(
            f'<button class="manual-gallery-dot{active_class}" type="button" '
            f'data-gallery-index="{index}" aria-label="Foto {index + 1}"></button>'
        )

    st.markdown(
        f"""
        <section class="manual-gallery-card" data-manual-gallery data-active="{current_index}">
            <button class="manual-gallery-hit" type="button" data-gallery-action="next" aria-label="Foto seguinte"></button>
            {''.join(slides)}
            <button class="manual-gallery-nav manual-gallery-prev" type="button" data-gallery-action="previous" aria-label="Foto anterior">&#8249;</button>
            <button class="manual-gallery-nav manual-gallery-next" type="button" data-gallery-action="next" aria-label="Foto seguinte">&#8250;</button>
            <div class="manual-gallery-controls" role="tablist">
                {''.join(dots)}
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    components.html(
        """
        <script>
            (() => {
                const doc = window.parent.document;
                const galleries = doc.querySelectorAll("[data-manual-gallery]");

                galleries.forEach((gallery) => {
                    if (gallery.dataset.galleryReady === "true") {
                        return;
                    }

                    gallery.dataset.galleryReady = "true";
                    const slides = Array.from(gallery.querySelectorAll(".manual-gallery-slide"));
                    const dots = Array.from(gallery.querySelectorAll(".manual-gallery-dot"));
                    let active = Number(gallery.dataset.active || 0);
                    let autoSlideTimer = null;

                    const showSlide = (target) => {
                        if (!slides.length) {
                            return;
                        }

                        active = (target + slides.length) % slides.length;
                        gallery.dataset.active = String(active);
                        slides.forEach((slide, index) => {
                            slide.classList.toggle("is-active", index === active);
                        });
                        dots.forEach((dot, index) => {
                            dot.classList.toggle("is-active", index === active);
                        });
                    };

                    const startAutoSlide = () => {
                        if (slides.length <= 1) {
                            return;
                        }

                        autoSlideTimer = window.setInterval(() => {
                            showSlide(active + 1);
                        }, 4500);
                    };

                    const restartAutoSlide = () => {
                        if (autoSlideTimer) {
                            window.clearInterval(autoSlideTimer);
                        }
                        startAutoSlide();
                    };

                    gallery.addEventListener("click", (event) => {
                        const control = event.target.closest("[data-gallery-action], [data-gallery-index]");

                        if (!control || !gallery.contains(control)) {
                            return;
                        }

                        event.preventDefault();
                        event.stopPropagation();

                        if (control.dataset.galleryIndex !== undefined) {
                            showSlide(Number(control.dataset.galleryIndex));
                            restartAutoSlide();
                            return;
                        }

                        showSlide(control.dataset.galleryAction === "previous" ? active - 1 : active + 1);
                        restartAutoSlide();
                    });

                    showSlide(active);
                    startAutoSlide();
                });
            })();
        </script>
        """,
        height=0,
        scrolling=False,
    )


def render_youtube_video() -> None:
    st.markdown(
        f"""
        <div class="video-panel">
            <iframe
                class="youtube-video"
                src="https://www.youtube.com/embed/{YOUTUBE_VIDEO_ID}?autoplay=1&mute=1&rel=0&controls=1&playsinline=1&loop=1&playlist={YOUTUBE_VIDEO_ID}"
                title="Chevrolet Equinox 2019 video"
                allow="autoplay; encrypted-media; picture-in-picture; web-share"
                allowfullscreen>
            </iframe>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_css() -> None:
    st.markdown(
        f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

            html, body, [class*="css"] {{
                font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            }}

            .stApp {{
                background:
                    radial-gradient(circle at 12% 8%, rgba(232, 49, 42, 0.13), transparent 30%),
                    radial-gradient(circle at 88% 15%, rgba(229, 184, 82, 0.18), transparent 28%),
                    linear-gradient(135deg, #fbfaf6 0%, #eef3f1 48%, #f5ede3 100%);
                color: #202326;
            }}

            [data-testid="stSidebar"] {{
                background:
                    linear-gradient(160deg, rgba(255, 255, 255, 0.96), rgba(240, 249, 244, 0.96) 54%, rgba(226, 244, 236, 0.94)),
                    #f5fbf7;
                border-right: 1px solid rgba(22, 160, 93, 0.18);
            }}

            [data-testid="stSidebar"] [data-testid="stSidebarContent"] {{
                padding: 1.25rem 1rem 1.5rem;
            }}

            .whatsapp-panel {{
                position: relative;
                overflow: hidden;
                padding: 1rem;
                border-radius: 8px;
                border: 1px solid rgba(22, 160, 93, 0.16);
                background:
                    linear-gradient(145deg, rgba(255, 255, 255, 0.98), rgba(237, 249, 243, 0.92)),
                    rgba(255, 255, 255, 0.92);
                box-shadow: 0 18px 44px rgba(24, 27, 31, 0.10);
            }}

            .whatsapp-panel::before {{
                content: "";
                position: absolute;
                inset: 0 0 auto;
                height: 3px;
                background: linear-gradient(90deg, #25d366, #ffd37c, #28c7b7);
            }}

            .whatsapp-kicker {{
                margin: 0 0 0.35rem;
                color: #25d366;
                font-size: 0.72rem;
                font-weight: 900;
                letter-spacing: 0;
                text-transform: uppercase;
            }}

            .whatsapp-panel h2 {{
                margin: 0 0 0.45rem;
                color: #153b31;
                font-size: 1.25rem;
                line-height: 1.12;
                font-weight: 900;
                letter-spacing: 0;
            }}

            .whatsapp-panel p {{
                margin: 0;
                color: rgba(32, 35, 38, 0.70);
                font-size: 0.88rem;
                line-height: 1.42;
            }}

            [data-testid="stSidebar"] .stTextArea {{
                margin-top: 0.75rem;
            }}

            [data-testid="stSidebar"] .stTextArea label {{
                color: #4bb3ff !important;
                font-size: 1.18rem !important;
                font-weight: 950 !important;
            }}

            [data-testid="stSidebar"] .stTextArea label p {{
                color: #4bb3ff !important;
                font-size: 1.18rem !important;
                font-weight: 950 !important;
            }}

            [data-testid="stSidebar"] textarea {{
                min-height: 150px !important;
                border-radius: 8px !important;
                border: 1px solid rgba(22, 160, 93, 0.18) !important;
                background: rgba(255, 255, 255, 0.98) !important;
                color: #11181c !important;
                font-weight: 650 !important;
                line-height: 1.45 !important;
                box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.72), 0 14px 30px rgba(24, 27, 31, 0.08) !important;
            }}

            [data-testid="stSidebar"] .stLinkButton a {{
                width: 100%;
                min-height: 3rem;
                border: 0 !important;
                border-radius: 8px !important;
                background: linear-gradient(135deg, #25d366, #0e9f63) !important;
                color: #ffffff !important;
                font-size: 1.18rem !important;
                font-weight: 950 !important;
                box-shadow: 0 18px 38px rgba(37, 211, 102, 0.24), 0 10px 22px rgba(0, 0, 0, 0.28) !important;
            }}

            [data-testid="stSidebar"] .stLinkButton a:hover {{
                border: 0 !important;
                background: linear-gradient(135deg, #2de276, #0b8756) !important;
                color: #ffffff !important;
                transform: translateY(-1px);
            }}

            .main .block-container {{
                max-width: 1260px;
                padding-top: 0 !important;
                padding-bottom: 3rem;
            }}

            .block-container,
            div[data-testid="stMainBlockContainer"],
            section[data-testid="stMain"] > div {{
                padding-top: 0 !important;
                margin-top: 0 !important;
            }}

            [data-testid="stHeader"] {{
                background: transparent;
                height: 0 !important;
                min-height: 0 !important;
            }}

            [data-testid="stHeader"],
            [data-testid="stToolbar"],
            [data-testid="stDecoration"],
            [data-testid="stStatusWidget"],
            [data-testid="collapsedControl"] {{
                display: none !important;
                height: 0 !important;
                min-height: 0 !important;
                visibility: hidden !important;
            }}

            .manual-gallery-card {{
                position: relative;
                width: 100%;
                aspect-ratio: 16 / 9;
                height: auto;
                margin: 0;
                overflow: hidden;
                border-radius: 8px;
                border: 1px solid rgba(255, 255, 255, 0.14);
                background: #060708;
                box-shadow: 0 20px 54px rgba(0, 0, 0, 0.24);
            }}

            .manual-gallery-slide {{
                position: absolute;
                inset: 0;
                display: grid;
                place-items: center;
                margin: 0;
                overflow: hidden;
                background: #060708;
                opacity: 0;
                pointer-events: none;
                transition: opacity 280ms ease;
            }}

            .manual-gallery-slide.is-active {{
                opacity: 1;
            }}

            .manual-gallery-slide img {{
                display: block;
                position: absolute;
                inset: 0;
                width: 100%;
                height: 100%;
                object-fit: contain;
                background: #060708;
                filter: saturate(1.06) contrast(1.03);
            }}

            .manual-gallery-hit {{
                position: absolute;
                inset: 0;
                z-index: 2;
                padding: 0;
                border: 0;
                background: transparent;
                appearance: none;
                cursor: pointer;
            }}

            .manual-gallery-nav {{
                position: absolute;
                top: 50%;
                z-index: 4;
                width: 2.75rem;
                height: 2.75rem;
                display: inline-grid;
                place-items: center;
                padding: 0;
                border: 1px solid rgba(255, 255, 255, 0.22);
                border-radius: 999px;
                background: rgba(6, 7, 8, 0.58);
                color: #ffffff !important;
                font-size: 2.15rem;
                line-height: 1;
                text-decoration: none !important;
                cursor: pointer;
                transform: translateY(-50%);
                box-shadow: 0 12px 28px rgba(0, 0, 0, 0.26);
            }}

            .manual-gallery-nav:hover {{
                background: rgba(22, 160, 93, 0.88);
                color: #ffffff !important;
            }}

            .manual-gallery-prev {{
                left: 0.85rem;
            }}

            .manual-gallery-next {{
                right: 0.85rem;
            }}

            .manual-gallery-controls {{
                position: absolute;
                left: 50%;
                bottom: 0.72rem;
                z-index: 5;
                display: flex;
                max-width: calc(100% - 2rem);
                gap: 0.38rem;
                padding: 0.48rem 0.58rem;
                overflow-x: auto;
                border-radius: 999px;
                background: rgba(6, 7, 8, 0.58);
                transform: translateX(-50%);
                box-shadow: 0 12px 28px rgba(0, 0, 0, 0.22);
            }}

            .manual-gallery-dot {{
                flex: 0 0 auto;
                display: block;
                width: 0.68rem;
                height: 0.68rem;
                padding: 0;
                border: 1px solid rgba(255, 255, 255, 0.55);
                border-radius: 999px;
                background: rgba(255, 255, 255, 0.46);
                appearance: none;
                cursor: pointer;
                transition: width 160ms ease, background 160ms ease, border-color 160ms ease;
            }}

            .manual-gallery-dot.is-active {{
                width: 1.6rem;
                border-color: #25d366;
                background: #25d366;
            }}

            div[data-testid="stElementContainer"]:has(.manual-gallery-card) {{
                margin-bottom: 0 !important;
            }}

            div[data-testid="stElementContainer"]:has(.manual-gallery-card) + div[data-testid="stElementContainer"]:has(.video-panel) {{
                margin-top: 0.25rem !important;
            }}

            div[data-testid="stElementContainer"]:has(iframe[title="st.iframe"]) {{
                height: 0 !important;
                min-height: 0 !important;
                margin: 0 !important;
                padding: 0 !important;
                overflow: hidden !important;
            }}

            iframe[title="st.iframe"] {{
                display: block !important;
                height: 0 !important;
                min-height: 0 !important;
            }}

            .hero {{
                padding: 0 0 0.45rem;
                border-bottom: 1px solid rgba(24, 27, 31, 0.12);
                margin-top: -1.15rem;
                margin-bottom: 0.65rem;
            }}

            .eyebrow {{
                display: inline-flex;
                align-items: center;
                gap: 0.5rem;
                padding: 0.48rem 0.78rem;
                border: 1px solid rgba(255, 255, 255, 0.18);
                border-radius: 999px;
                background: rgba(255, 255, 255, 0.08);
                color: #ffd37c;
                font-weight: 800;
                font-size: 0.78rem;
                text-transform: uppercase;
                letter-spacing: 0;
            }}

            .hero-heading {{
                display: grid;
                grid-template-columns: auto minmax(0, 1fr) auto;
                align-items: center;
                gap: clamp(0.65rem, 2vw, 1.35rem);
                color: #181b1f;
            }}

            .hero h1 {{
                display: flex;
                align-items: center;
                flex-wrap: nowrap;
                margin: 0;
                color: #181b1f;
                font-size: clamp(1.85rem, 4.8vw, 4.45rem);
                line-height: 0.92;
                font-weight: 900;
                letter-spacing: 0;
                white-space: nowrap;
            }}

            .header-qr-frame {{
                width: auto;
                height: clamp(2.75rem, 6.4vw, 5.35rem);
                aspect-ratio: 1;
                flex: 0 0 auto;
                padding: 0.24rem;
                border-radius: 8px;
                border: 1px solid rgba(24, 27, 31, 0.16);
                background: #ffffff;
                box-shadow: 0 12px 24px rgba(24, 27, 31, 0.14);
            }}

            .header-qr-frame img {{
                width: 100%;
                height: 100%;
                object-fit: contain;
                display: block;
            }}

            .hero h1 span {{
                color: #e8312a;
                text-shadow: 0 16px 45px rgba(232, 49, 42, 0.35);
            }}

            .hero-contact {{
                justify-self: end;
                display: flex;
                flex-direction: column;
                align-items: flex-end;
                gap: 0.28rem;
            }}

            .slogan-text {{
                margin: 0;
                color: #16a05d !important;
                font-size: clamp(1rem, 1.55vw, 1.32rem) !important;
                font-weight: 950 !important;
                line-height: 1.15 !important;
                text-align: right;
                white-space: nowrap;
            }}

            .hero-whatsapp-button {{
                display: inline-flex;
                align-items: center;
                justify-content: center;
                min-height: 2.1rem;
                padding: 0.48rem 0.72rem;
                border-radius: 8px;
                background: linear-gradient(135deg, #25d366, #0e9f63);
                color: #ffffff !important;
                font-size: clamp(0.72rem, 1vw, 0.88rem);
                font-weight: 900;
                line-height: 1;
                text-decoration: none !important;
                white-space: nowrap;
                box-shadow: 0 12px 24px rgba(37, 211, 102, 0.22);
            }}

            .hero-whatsapp-button:hover {{
                background: linear-gradient(135deg, #2de276, #0b8756);
                color: #ffffff !important;
            }}

            .hero-copy {{
                max-width: 820px;
                color: rgba(247, 243, 234, 0.82);
                font-size: clamp(1rem, 2vw, 1.28rem);
                line-height: 1.55;
                margin: 0;
            }}

            .hero-strip {{
                display: grid;
                grid-template-columns: repeat(4, minmax(0, 1fr));
                gap: 0.8rem;
                margin-top: 1.35rem;
            }}

            .metric {{
                border-radius: 8px;
                padding: 1rem;
                border: 1px solid rgba(24, 27, 31, 0.10);
                background: rgba(255, 255, 255, 0.78);
                box-shadow: 0 18px 50px rgba(24, 27, 31, 0.10);
                min-height: 96px;
            }}

            .metric strong {{
                display: block;
                color: #181b1f;
                font-size: 1.25rem;
                line-height: 1.1;
                margin-bottom: 0.35rem;
            }}

            .metric span {{
                color: rgba(32, 35, 38, 0.68);
                font-size: 0.88rem;
                line-height: 1.35;
            }}

            .section-title {{
                color: #181b1f;
                font-size: 1.2rem;
                font-weight: 850;
                margin: 0 0 0.75rem;
            }}

            .video-panel {{
                border-radius: 8px;
                padding: 1rem;
                border: 1px solid rgba(24, 27, 31, 0.11);
                background: rgba(255, 255, 255, 0.82);
                box-shadow: 0 24px 70px rgba(24, 27, 31, 0.14);
                min-height: 430px;
                margin-bottom: 0;
            }}

            .video-caption {{
                color: rgba(32, 35, 38, 0.68);
                font-size: 0.92rem;
                line-height: 1.45;
                margin: 0.6rem 0 0;
            }}

            .youtube-video {{
                display: block;
                width: 100%;
                height: 430px;
                border: 0;
                border-radius: 8px;
                background: #060708;
            }}

            .video-link-card {{
                display: flex;
                flex-direction: column;
                justify-content: center;
                min-height: 230px;
                padding: 1.25rem;
                border-radius: 8px;
                border: 1px solid rgba(255, 255, 255, 0.14);
                background:
                    linear-gradient(145deg, rgba(232, 49, 42, 0.16), rgba(255, 211, 124, 0.10)),
                    rgba(8, 9, 11, 0.72);
                color: #fff9eb !important;
                text-decoration: none !important;
                box-shadow: 0 22px 60px rgba(0, 0, 0, 0.32);
                transition: transform 160ms ease, border-color 160ms ease, background 160ms ease;
            }}

            .video-link-card:hover {{
                transform: translateY(-2px);
                border-color: rgba(255, 211, 124, 0.42);
                background:
                    linear-gradient(145deg, rgba(232, 49, 42, 0.22), rgba(40, 199, 183, 0.12)),
                    rgba(8, 9, 11, 0.82);
            }}

            .video-link-card strong {{
                color: #ffffff;
                font-size: 1.18rem;
                line-height: 1.25;
                margin: 0.45rem 0 0.55rem;
                word-break: break-word;
            }}

            .video-link-card span {{
                color: rgba(247, 243, 234, 0.74);
                font-size: 0.95rem;
            }}

            .video-link-card .video-link-kicker {{
                color: #ffd37c;
                font-size: 0.76rem;
                font-weight: 900;
                text-transform: uppercase;
            }}

            .marketing-grid {{
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 0.9rem;
                margin-top: 1.35rem;
            }}

            .promo-card {{
                position: relative;
                overflow: hidden;
                min-height: 180px;
                padding: 1.25rem;
                border-radius: 8px;
                border: 1px solid rgba(24, 27, 31, 0.11);
                background:
                    linear-gradient(145deg, rgba(255, 255, 255, 0.96), rgba(255, 250, 241, 0.84)),
                    rgba(255, 255, 255, 0.86);
                box-shadow: 0 18px 55px rgba(24, 27, 31, 0.11);
            }}

            .promo-card::before {{
                content: "";
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 3px;
                background: linear-gradient(90deg, #e8312a, #ffd37c, #28c7b7);
            }}

            .promo-card small {{
                display: inline-block;
                color: #ffd37c;
                font-weight: 850;
                text-transform: uppercase;
                font-size: 0.72rem;
                margin-bottom: 0.55rem;
            }}

            .promo-card h3 {{
                margin: 0 0 0.55rem;
                color: #181b1f;
                font-size: 1.35rem;
                line-height: 1.1;
                font-weight: 880;
                letter-spacing: 0;
            }}

            .promo-card p {{
                margin: 0;
                color: rgba(32, 35, 38, 0.72);
                line-height: 1.5;
                font-size: 0.95rem;
            }}

            .site-footer {{
                margin-top: 1.15rem;
                padding: 1.15rem;
                display: grid;
                grid-template-columns: minmax(0, 1fr) auto;
                gap: 1rem;
                align-items: center;
                border-radius: 8px;
                border: 1px solid rgba(24, 27, 31, 0.11);
                background:
                    linear-gradient(135deg, rgba(255, 255, 255, 0.94), rgba(240, 249, 244, 0.86)),
                    rgba(255, 255, 255, 0.86);
                box-shadow: 0 20px 60px rgba(24, 27, 31, 0.11);
            }}

            .site-footer h2 {{
                margin: 0 0 0.35rem;
                color: #181b1f;
                font-size: clamp(1.35rem, 2.2vw, 2.1rem);
                line-height: 1.05;
                font-weight: 920;
                letter-spacing: 0;
            }}

            .site-footer p {{
                margin: 0;
                max-width: 680px;
                color: rgba(32, 35, 38, 0.70);
                font-size: 0.96rem;
                line-height: 1.48;
            }}

            .footer-trust {{
                display: flex;
                flex-wrap: wrap;
                gap: 0.45rem;
                margin-top: 0.85rem;
            }}

            .footer-trust span {{
                display: inline-flex;
                align-items: center;
                min-height: 2rem;
                padding: 0.4rem 0.64rem;
                border-radius: 999px;
                border: 1px solid rgba(22, 160, 93, 0.18);
                background: rgba(255, 255, 255, 0.72);
                color: rgba(32, 35, 38, 0.76);
                font-size: 0.78rem;
                font-weight: 850;
                white-space: nowrap;
            }}

            .footer-contact {{
                display: flex;
                align-items: center;
                gap: 0.85rem;
            }}

            .footer-qr-frame {{
                width: clamp(5.2rem, 8vw, 6.8rem);
                aspect-ratio: 1;
                padding: 0.32rem;
                border-radius: 8px;
                border: 1px solid rgba(24, 27, 31, 0.14);
                background: #ffffff;
                box-shadow: 0 14px 30px rgba(24, 27, 31, 0.12);
            }}

            .footer-qr-frame img {{
                width: 100%;
                height: 100%;
                display: block;
                object-fit: contain;
            }}

            .footer-actions {{
                display: flex;
                flex-direction: column;
                align-items: stretch;
                gap: 0.45rem;
                min-width: 170px;
            }}

            .footer-whatsapp-label {{
                color: #16a05d;
                font-size: 0.88rem;
                font-weight: 950;
                line-height: 1;
            }}

            .footer-whatsapp-button {{
                display: inline-flex;
                align-items: center;
                justify-content: center;
                min-height: 2.65rem;
                padding: 0.66rem 0.9rem;
                border-radius: 8px;
                background: linear-gradient(135deg, #25d366, #0e9f63);
                color: #ffffff !important;
                font-size: 0.9rem;
                font-weight: 920;
                text-decoration: none !important;
                white-space: nowrap;
                box-shadow: 0 14px 28px rgba(37, 211, 102, 0.22);
            }}

            .footer-whatsapp-button:hover {{
                background: linear-gradient(135deg, #2de276, #0b8756);
                color: #ffffff !important;
            }}

            .cta-band {{
                margin-top: 1.25rem;
                display: grid;
                grid-template-columns: 1.4fr 0.6fr;
                gap: 0.9rem;
                align-items: stretch;
            }}

            .cta-main, .cta-side {{
                border-radius: 8px;
                border: 1px solid rgba(24, 27, 31, 0.11);
                background: rgba(255, 255, 255, 0.78);
                padding: 1.35rem;
            }}

            .cta-main h2 {{
                margin: 0 0 0.45rem;
                color: #181b1f;
                font-weight: 900;
                font-size: 1.8rem;
                letter-spacing: 0;
            }}

            .cta-main p, .cta-side p {{
                margin: 0;
                color: rgba(32, 35, 38, 0.72);
                line-height: 1.5;
            }}

            .cta-side strong {{
                display: block;
                color: #ffd37c;
                font-size: 1.1rem;
                margin-bottom: 0.35rem;
            }}

            .empty-state {{
                padding: 2rem;
                border: 1px dashed rgba(255, 255, 255, 0.25);
                border-radius: 8px;
                color: rgba(247, 243, 234, 0.75);
            }}

            div[data-testid="stVideo"] {{
                overflow: hidden;
                border-radius: 8px;
                border: 1px solid rgba(255, 255, 255, 0.12);
                background: #060708;
                box-shadow: 0 24px 70px rgba(0, 0, 0, 0.34);
            }}

            div[data-testid="stVideo"] video {{
                width: 100% !important;
                height: 430px !important;
                object-fit: contain !important;
                background: #060708;
            }}

            div[data-testid="stVideo"] + div .video-caption {{
                margin-top: 0.75rem;
            }}

            @media (max-width: 900px) {{
                .hero-strip,
                .marketing-grid,
                .site-footer,
                .cta-band {{
                    grid-template-columns: 1fr;
                }}

                .hero {{
                    padding-top: 1rem;
                }}

                .hero-heading {{
                    grid-template-columns: auto minmax(0, 1fr) auto;
                    align-items: center;
                    gap: 0.35rem;
                }}

                .hero h1 {{
                    font-size: clamp(1.12rem, 8vw, 2rem);
                }}

                .slogan-text {{
                    font-size: clamp(0.78rem, 2.6vw, 1rem) !important;
                }}

                .hero-whatsapp-button {{
                    min-height: 1.95rem;
                    padding: 0.42rem 0.58rem;
                    font-size: clamp(0.64rem, 2.1vw, 0.76rem);
                }}

                .header-qr-frame {{
                    height: clamp(3rem, 15vw, 4.4rem);
                }}

                .manual-gallery-card {{
                    height: clamp(210px, 58vw, 360px);
                }}

                div[data-testid="stElementContainer"]:has(.manual-gallery-card) + div[data-testid="stElementContainer"]:has(.video-panel) {{
                    margin-top: 0.2rem !important;
                }}

                .manual-gallery-nav {{
                    width: 2.35rem;
                    height: 2.35rem;
                    font-size: 1.8rem;
                }}

                .manual-gallery-prev {{
                    left: 0.45rem;
                }}

                .manual-gallery-next {{
                    right: 0.45rem;
                }}

                .video-panel {{
                    min-height: 0;
                    padding: 0.55rem;
                }}

                .youtube-video {{
                    aspect-ratio: 16 / 9;
                    height: min(52vw, 430px);
                }}

                .marketing-grid {{
                    margin-top: 0.35rem;
                }}

                .site-footer {{
                    margin-top: 0.8rem;
                    padding: 0.9rem;
                    gap: 0.85rem;
                }}

                .footer-contact {{
                    justify-content: space-between;
                    align-items: center;
                }}

                .footer-qr-frame {{
                    width: clamp(4.7rem, 22vw, 5.7rem);
                }}

                .footer-actions {{
                    min-width: 0;
                    flex: 1;
                }}
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    qr_data_uri = file_data_uri(discover_qr_code())
    contact_url = whatsapp_url()
    st.markdown(
        f"""
        <section class="hero">
            <div class="hero-heading">
                <h1>
                    Chevy <span>Equinox</span>
                </h1>
                <div class="hero-contact">
                    <p class="slogan-text">Whatsapp</p>
                    <a class="hero-whatsapp-button" href="{contact_url}" target="_blank" rel="noopener noreferrer">Enviar Mensagem</a>
                </div>
                <div class="header-qr-frame">
                    <img src="{qr_data_uri}" alt="QR-Code para contacto" />
                </div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_whatsapp_sidebar() -> None:
    st.sidebar.markdown(
        """
        <section class="whatsapp-panel">
            <p class="whatsapp-kicker">Contacto rápido</p>
            <h2>Enviar mensagem</h2>
            <p>Personalize o texto e abra diretamente no WhatsApp.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )
    message = st.sidebar.text_area(
        "Mensagem",
        value=DEFAULT_WHATSAPP_MESSAGE,
        height=160,
        key="whatsapp_message",
    )
    st.sidebar.link_button(
        "Enviar pelo WhatsApp",
        whatsapp_url(message),
        use_container_width=True,
        type="primary",
    )


def render_marketing_cards() -> None:
    st.markdown(
        """
        <section class="marketing-grid">
            <article class="promo-card">
                <small>Conforto</small>
                <h3>Feito para viajar bem</h3>
                <p>Cabine ampla e agradável para conduzir com tranquilidade, seja no dia a dia ou em percursos longos.</p>
            </article>
            <article class="promo-card">
                <small>Estilo de vida</small>
                <h3>Mais que transporte</h3>
                <p>É o tipo de carro que combina com família, negócios, lazer e aquela vontade boa de conduzir algo melhor.</p>
            </article>
            <article class="promo-card">
                <small>Confiança</small>
                <h3>Visual bem cuidado</h3>
                <p>As imagens e vídeos destacam detalhes reais do veículo para passar transparência e despertar desejo.</p>
            </article>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    qr_data_uri = file_data_uri(discover_qr_code())
    contact_url = whatsapp_url()
    st.markdown(
        f"""
        <footer class="site-footer">
            <div>
                <h2 style="color: blue;">Chevy Equinox de perto</h2>
                <p>Entre em contacto pelo WhatsApp e combine uma conversa direta, com detalhes do veículo num só lugar.</p>
                <!--
                <div class="footer-trust" aria-label="Destaques do atendimento">
                    <span>Contacto direto</span>
                    <span>Fotos reais do veículo</span>
                    <span>Resposta prática</span>
                </div>
                -->
            </div>
            <div class="footer-contact">
                <div class="footer-qr-frame">
                    <img src="{qr_data_uri}" alt="QR-Code para contacto" />
                </div>
                <div class="footer-actions">
                    <span class="footer-whatsapp-label">Whatsapp</span>
                    <a class="footer-whatsapp-button" href="{contact_url}" target="_blank" rel="noopener noreferrer">Enviar Mensagem</a>
                </div>
            </div>
        </footer>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(
        page_title="Chevrolet Equinox",
        page_icon="",
        layout="wide",
        initial_sidebar_state="auto",
    )

    images = discover_assets(IMAGE_EXTENSIONS)
    render_css()
    render_whatsapp_sidebar()
    render_hero()

    if GALLERY_VIDEO_POSITION <= 1:
        render_youtube_video()
        render_photo_gallery(images)
    else:
        render_photo_gallery(images)
        render_youtube_video()

    render_marketing_cards()
    render_footer()


if __name__ == "__main__":
    main()
