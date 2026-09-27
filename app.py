from __future__ import annotations

import streamlit as st

from ott_brain.database import ensure_database
from ott_brain.feedback import add_feedback, list_rejections
from ott_brain.movies import sync_movie_metadata
from ott_brain.onboarding import (
    complete_onboarding,
    onboarding_complete,
    skip_onboarding,
    subscriptions_configured,
)
from ott_brain.providers_service import providers_last_checked, sync_providers
from ott_brain.subscriptions import all_services, get_subscribed_slugs, set_subscribed_slugs
from ott_brain.tmdb import TmdbError, poster_url, search_movies
from ott_brain.watch_history import (
    bulk_import_titles,
    list_watch_history,
    mark_watched,
    update_watch_entry,
)

st.set_page_config(page_title="OTT Brain", page_icon="🎬", layout="wide")

ensure_database()


def render_subscription_toggles(location: str) -> None:
    subscribed = get_subscribed_slugs()
    st.subheader("My streaming services (India)")
    chosen: set[str] = set()
    for svc in all_services():
        if st.checkbox(
            svc.label,
            value=svc.slug in subscribed,
            key=f"{location}_ott_{svc.slug}",
        ):
            chosen.add(svc.slug)
    if st.button("Save subscriptions", key=f"{location}_save_ott"):
        set_subscribed_slugs(chosen)
        st.success("Subscriptions saved.")


def render_onboarding() -> None:
    step = st.session_state.get("onboarding_step", 0)
    st.header("Welcome to OTT Brain")

    if step == 0:
        st.write("**Step 1 of 3** — Choose your Indian streaming services.")
        render_subscription_toggles("onboarding")
        if st.button("Next", type="primary", key="onb_next_0"):
            if not get_subscribed_slugs():
                st.warning(
                    "No services selected — you can add them later, but "
                    "availability filtering needs at least one subscription."
                )
            st.session_state["onboarding_step"] = 1
            st.rerun()
        if st.button("Skip setup", key="onb_skip_all"):
            skip_onboarding()
            st.rerun()
        return

    if step == 1:
        st.write("**Step 2 of 3** — Paste watched titles (optional, one per line).")
        bulk_text = st.text_area("Titles", height=100, key="onb_bulk")
        if st.button("Import & continue", key="onb_import"):
            if bulk_text.strip():
                try:
                    result = bulk_import_titles(bulk_text.splitlines())
                    st.success(
                        f"Imported {len(result.resolved)}; "
                        f"{len(result.ambiguous)} ambiguous; "
                        f"{len(result.failed)} failed."
                    )
                except (TmdbError, ValueError) as exc:
                    st.error(str(exc))
                    return
            st.session_state["onboarding_step"] = 2
            st.rerun()
        if st.button("Skip import", key="onb_skip_import"):
            st.session_state["onboarding_step"] = 2
            st.rerun()
        return

    st.write("**Step 3 of 3** — Rate up to 10 favorites (optional).")
    entries = list_watch_history()[:10]
    if not entries:
        st.caption("No movies yet — you can rate titles later in History.")
    for entry in entries:
        cols = st.columns([3, 1, 1])
        with cols[0]:
            st.markdown(f"{entry['title']} ({entry['year'] or '?'})")
        with cols[1]:
            st.number_input(
                "Rating",
                0.0,
                10.0,
                float(entry["rating"] or 0.0),
                key=f"onb_rate_{entry['movie_id']}",
            )
        with cols[2]:
            st.checkbox("Loved", key=f"onb_loved_{entry['movie_id']}")

    def _finish_onboarding(save_ratings: bool) -> None:
        if save_ratings:
            for entry in entries:
                mid = entry["movie_id"]
                rating = float(st.session_state.get(f"onb_rate_{mid}", 0.0))
                loved = bool(st.session_state.get(f"onb_loved_{mid}", False))
                if rating > 0 or loved:
                    update_watch_entry(
                        mid,
                        rating=rating if rating > 0 else None,
                        liked=loved,
                    )
                    if loved:
                        add_feedback(mid, "LOVED")
        complete_onboarding()
        st.session_state.pop("onboarding_step", None)
        st.rerun()

    if st.button("Save ratings & finish", type="primary", key="onb_finish"):
        _finish_onboarding(save_ratings=True)
    if st.button("Dismiss rating", key="onb_dismiss_rate"):
        _finish_onboarding(save_ratings=False)


def render_home() -> None:
    st.header("Home")
    if not subscriptions_configured():
        st.warning(
            "No OTT subscriptions selected — recommendations will not filter by "
            "your catalogs until you pick services below or in Settings."
        )
    st.caption("What do you want to watch tonight?")
    st.text_area(
        "Ask in plain language (coming in Epic E4)",
        placeholder="e.g. dark psychological thriller under 2 hours",
        height=100,
        disabled=True,
        key="nl_query_placeholder",
    )
    st.divider()
    render_subscription_toggles("home")
    st.divider()
    st.subheader("Find a movie")
    query = st.text_input("Search TMDB (movies only)", key="movie_search_query")
    if query:
        try:
            results = search_movies(query)
        except ValueError as exc:
            st.error(str(exc))
            return
        except TmdbError as exc:
            st.error(str(exc))
            return

        if not results:
            st.info("No movies found for that title.")
            return

        for item in results:
            cols = st.columns([1, 4, 2])
            with cols[0]:
                url = poster_url(item.poster_path)
                if url:
                    st.image(url, width=100)
                else:
                    st.caption("No poster")
            with cols[1]:
                year = f" ({item.year})" if item.year else ""
                st.markdown(f"**{item.title}**{year}")
                if item.overview:
                    st.caption(item.overview[:220] + ("…" if len(item.overview) > 220 else ""))
            with cols[2]:
                if st.button("Save", key=f"save_{item.tmdb_id}"):
                    try:
                        sync_movie_metadata(item.tmdb_id, force=True)
                        sync_providers(item.tmdb_id, force=True)
                        st.success(f"Saved {item.title} (metadata + IN providers).")
                    except TmdbError as exc:
                        st.error(str(exc))
                if st.button("Watched", key=f"watched_{item.tmdb_id}"):
                    try:
                        sync_movie_metadata(item.tmdb_id, force=True)
                        mark_watched(item.tmdb_id)
                        st.success(f"Marked {item.title} as watched.")
                    except (TmdbError, ValueError) as exc:
                        st.error(str(exc))
                last = providers_last_checked(item.tmdb_id)
                if last:
                    st.caption(f"Providers checked: {last[:10]}")


def render_recommendations() -> None:
    st.header("Recommendations")
    st.info("Ranked picks arrive in Epic E6. Discovery pipeline lands in E4–E5.")


def render_history() -> None:
    st.header("History")
    st.subheader("Watched")
    entries = list_watch_history()
    if not entries:
        st.caption("No watched titles yet — search on Home or use bulk import below.")
    for entry in entries:
        cols = st.columns([3, 1, 1, 1])
        with cols[0]:
            st.markdown(f"**{entry['title']}** ({entry['year'] or '?'})")
            st.caption(entry["watched_at"][:10])
        with cols[1]:
            rating = st.number_input(
                "Rating",
                min_value=0.0,
                max_value=10.0,
                value=float(entry["rating"] or 0.0),
                key=f"rate_{entry['movie_id']}",
            )
        with cols[2]:
            loved = st.checkbox("Loved", key=f"loved_{entry['movie_id']}")
            liked = st.checkbox("Liked", key=f"liked_{entry['movie_id']}")
        with cols[3]:
            if st.button("Update", key=f"upd_{entry['movie_id']}"):
                update_watch_entry(
                    entry["movie_id"],
                    rating=rating if rating > 0 else None,
                    liked=loved or liked,
                )
                if loved:
                    add_feedback(entry["movie_id"], "LOVED")
                elif liked:
                    add_feedback(entry["movie_id"], "LIKED")
                st.success("Updated.")
            if st.button("Reject", key=f"rej_{entry['movie_id']}"):
                add_feedback(entry["movie_id"], "NOT_INTERESTED")
                st.warning("Marked as rejected.")

    st.divider()
    st.subheader("Rejected")
    rejections = list_rejections()
    if rejections:
        for row in rejections:
            st.text(f"{row['title']} ({row['year'] or '?'}) — {row['type']}")
    else:
        st.caption("No rejections yet.")

    st.divider()
    st.subheader("Bulk import watched list")
    st.caption("One movie title per line. Ambiguous matches can be picked below.")
    bulk_text = st.text_area("Titles", height=120, key="bulk_titles")
    if st.button("Import", key="bulk_import"):
        lines = bulk_text.splitlines()
        try:
            result = bulk_import_titles(lines)
        except (TmdbError, ValueError) as exc:
            st.error(str(exc))
            return
        if result.resolved:
            st.success(f"Resolved {len(result.resolved)} title(s).")
            for row in result.resolved:
                st.write(f"✓ {row.line} → {row.title}")
        if result.failed:
            st.warning(f"Failed {len(result.failed)} title(s).")
            for row in result.failed:
                st.write(f"✗ {row.line}")
        if result.ambiguous:
            st.info(f"Ambiguous {len(result.ambiguous)} title(s) — pick a match:")
            for amb in result.ambiguous:
                st.markdown(f"**{amb.line}**")
                for cand in amb.candidates:
                    label = f"{cand['title']} ({cand.get('year') or '?'})"
                    if st.button(label, key=f"bulk_{amb.line}_{cand['tmdb_id']}"):
                        mark_watched(cand["tmdb_id"])
                        st.success(f"Added {label}")


def render_settings() -> None:
    st.header("Settings")
    render_subscription_toggles("settings")


def main() -> None:
    st.sidebar.title("OTT Brain")
    if not onboarding_complete():
        render_onboarding()
        return

    page = st.sidebar.radio(
        "Navigate",
        ["Home", "Recommendations", "History", "Settings"],
        index=0,
    )
    st.sidebar.caption("Single-user · no login")

    if page == "Home":
        render_home()
    elif page == "Recommendations":
        render_recommendations()
    elif page == "History":
        render_history()
    else:
        render_settings()


if __name__ == "__main__":
    main()
