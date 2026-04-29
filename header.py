from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from flask import Blueprint, url_for
from markupsafe import Markup, escape

shared_media = Blueprint(
    "shared_media",
    __name__,
    static_folder="media",
    static_url_path="/shared/media",
)


def _user_initials(user: Any) -> str:
    if user is None:
        return "U"

    display_name = str(getattr(user, "display_name", "") or getattr(user, "email", "") or "").strip()
    parts = [part for part in display_name.split() if part]
    if len(parts) > 1:
        return f"{parts[0][0]}{parts[-1][0]}".upper()
    if parts:
        return parts[0][0].upper()
    return "U"


def _normalize_links(items: Iterable[Any] | None) -> list[tuple[str, str]]:
    normalized: list[tuple[str, str]] = []
    if not items:
        return normalized

    for item in items:
        label = ""
        href = ""
        if isinstance(item, dict):
            label = str(item.get("label", "") or "")
            href = str(item.get("href", "") or "")
        elif isinstance(item, (tuple, list)) and len(item) >= 2:
            label = str(item[0] or "")
            href = str(item[1] or "")
        if label and href:
            normalized.append((label, href))
    return normalized


def _normalize_actions(items: Iterable[Any] | None) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    if not items:
        return normalized

    for item in items:
        label = ""
        action = ""
        method = "post"
        if isinstance(item, dict):
            label = str(item.get("label", "") or "")
            action = str(item.get("action", "") or item.get("href", "") or "")
            method = str(item.get("method", "post") or "post").lower()
        elif isinstance(item, (tuple, list)) and len(item) >= 2:
            label = str(item[0] or "")
            action = str(item[1] or "")
            if len(item) >= 3:
                method = str(item[2] or "post").lower()
        if label and action:
            normalized.append({"label": label, "action": action, "method": method})
    return normalized


def _render_styles() -> str:
    return """
<style>
.cp-app-header {
  background: linear-gradient(180deg, #2a2d31 0%, #222529 100%);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  color: #f4f6f8;
}

.cp-app-header-inner {
  display: grid;
  grid-template-columns: minmax(92px, auto) 1fr minmax(92px, auto);
  align-items: center;
  gap: 12px;
  max-width: 1280px;
  margin: 0 auto;
  padding: 14px 18px 10px;
}

.cp-app-header-logo-link,
.cp-app-header-title,
.cp-app-header-user-button,
.cp-app-header-home,
.cp-app-header-link {
  color: inherit;
}

.cp-app-header-logo {
  display: block;
  width: auto;
  height: 30px;
  max-width: 110px;
  object-fit: contain;
}

.cp-app-header-title-wrap {
  min-width: 0;
  text-align: center;
}

.cp-app-header-title {
  display: inline-block;
  font-size: 1.15rem;
  font-weight: 700;
  letter-spacing: 0;
  line-height: 1.2;
  white-space: nowrap;
}

.cp-app-header-user {
  justify-self: end;
  position: relative;
}

.cp-app-header-user-spacer {
  width: 42px;
  height: 42px;
}

.cp-app-header-user-button {
  width: 42px;
  height: 42px;
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  padding: 0;
}

.cp-app-header-user-button-static {
  cursor: default;
}

.cp-app-header-roundel {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.12);
  font-size: 0.85rem;
  font-weight: 700;
  line-height: 1;
}

.cp-app-header-menu {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  min-width: 160px;
  background: #1f2226;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 12px;
  box-shadow: 0 16px 36px rgba(0, 0, 0, 0.32);
  padding: 6px;
  z-index: 40;
}

.cp-app-header-menu[hidden] {
  display: none;
}

.cp-app-header-menu-link {
  display: block;
  padding: 10px 12px;
  border-radius: 8px;
  color: #f4f6f8;
  text-decoration: none;
  line-height: 1.2;
}

.cp-app-header-menu-link:hover,
.cp-app-header-menu-link:focus-visible {
  background: rgba(255, 255, 255, 0.08);
  outline: none;
}

.cp-app-header-nav {
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 18px 12px;
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.cp-app-header-home,
.cp-app-header-link {
  display: inline-flex;
  align-items: center;
  min-height: 32px;
  padding: 0 12px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  text-decoration: none;
  font-size: 0.95rem;
  font-weight: 600;
  background: rgba(255, 255, 255, 0.05);
}

.cp-app-header-home:hover,
.cp-app-header-home:focus-visible,
.cp-app-header-link:hover,
.cp-app-header-link:focus-visible {
  background: rgba(255, 255, 255, 0.11);
  outline: none;
}

.cp-app-header-form {
  margin: 0;
}

@media (max-width: 720px) {
  .cp-app-header-inner {
    grid-template-columns: auto 1fr auto;
    padding-inline: 14px;
  }

  .cp-app-header-logo {
    height: 26px;
    max-width: 90px;
  }

  .cp-app-header-title {
    font-size: 1rem;
  }

  .cp-app-header-nav {
    padding-inline: 14px;
  }
}
</style>
"""


def _render_user_menu(user: Any, user_menu_items: Iterable[Any] | None) -> str:
    initials = escape(_user_initials(user))
    user_label = escape(str(getattr(user, "display_name", "") or getattr(user, "email", "") or "User"))
    items = _normalize_links(user_menu_items)

    if not items:
        return f"""
    <div class="cp-app-header-user" aria-label="{user_label}">
      <div
        class="cp-app-header-user-button cp-app-header-user-button-static"
        title="{user_label}"
        aria-label="{user_label}"
      >
        <span class="cp-app-header-roundel" aria-hidden="true">{initials}</span>
      </div>
    </div>
    """

    menu_links = "".join(
        f'<a class="cp-app-header-menu-link" role="menuitem" href="{escape(href)}">{escape(label)}</a>'
        for label, href in items
    )

    return f"""
    <div class="cp-app-header-user">
      <button
        type="button"
        class="cp-app-header-user-button"
        data-cp-header-user-button
        aria-haspopup="true"
        aria-expanded="false"
        aria-controls="cp-header-user-menu"
        title="{user_label}"
        aria-label="{user_label}"
      >
        <span class="cp-app-header-roundel" aria-hidden="true">{initials}</span>
      </button>
      <div class="cp-app-header-menu" id="cp-header-user-menu" role="menu" hidden>
        {menu_links}
      </div>
    </div>
    """


def _render_script() -> str:
    return """
<script>
(function () {
  function closeMenus() {
    document.querySelectorAll("[data-cp-header-user-button]").forEach(function (button) {
      var menu = button.parentElement ? button.parentElement.querySelector(".cp-app-header-menu") : null;
      if (menu) {
        menu.hidden = true;
      }
      button.setAttribute("aria-expanded", "false");
    });
  }

  document.addEventListener("click", function (event) {
    var button = event.target.closest("[data-cp-header-user-button]");
    if (button) {
      var menu = button.parentElement ? button.parentElement.querySelector(".cp-app-header-menu") : null;
      if (!menu) {
        return;
      }
      var isOpen = !menu.hidden;
      closeMenus();
      menu.hidden = isOpen;
      button.setAttribute("aria-expanded", String(!isOpen));
      event.stopPropagation();
      return;
    }

    if (!event.target.closest(".cp-app-header-user")) {
      closeMenus();
    }
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      closeMenus();
    }
  });
})();
</script>
"""


def render_shared_header(
    *,
    app_name: str,
    home_href: str,
    primary_links: Iterable[Any] | None = None,
    primary_actions: Iterable[Any] | None = None,
    current_user: Any = None,
    auth_enabled: bool = True,
    user_menu_items: Iterable[Any] | None = None,
    home_label: str = "Home",
    logo_filename: str = "CPC-Logo.png",
) -> Markup:
    logo_href = url_for("shared_media.static", filename=logo_filename)
    nav_links = _normalize_links(primary_links)
    nav_actions = _normalize_actions(primary_actions)
    if auth_enabled and current_user is not None:
        user_menu_html = _render_user_menu(current_user, user_menu_items)
    else:
        user_menu_html = '<div class="cp-app-header-user-spacer" aria-hidden="true"></div>'
    link_html = "".join(
        f'<a class="cp-app-header-link" href="{escape(href)}">{escape(label)}</a>'
        for label, href in nav_links
    )
    action_html = "".join(
        f'<form class="cp-app-header-form" method="{escape(item["method"])}" action="{escape(item["action"])}"><button class="cp-app-header-link" type="submit">{escape(item["label"])}</button></form>'
        for item in nav_actions
    )

    return Markup(
        f"""
{_render_styles()}
<header class="cp-app-header">
  <div class="cp-app-header-inner">
    <a class="cp-app-header-logo-link" href="{escape(home_href)}" aria-label="Home">
      <img class="cp-app-header-logo" src="{escape(logo_href)}" alt="Cambridge Picture">
    </a>
    <div class="cp-app-header-title-wrap">
      <span class="cp-app-header-title">{escape(app_name)}</span>
    </div>
    {user_menu_html}
  </div>
  <nav class="cp-app-header-nav" aria-label="App navigation">
    <a class="cp-app-header-home" href="{escape(home_href)}">{escape(home_label)}</a>
    {link_html}
    {action_html}
  </nav>
</header>
{_render_script()}
"""
    )


def install_shared_header(app, *, auth_enabled: bool = True) -> None:
    if "shared_media" not in app.blueprints:
        app.register_blueprint(shared_media)

    @app.context_processor
    def inject_shared_header_helpers():
        return {
            "render_shared_header": render_shared_header,
            "shared_auth_enabled": auth_enabled,
        }
