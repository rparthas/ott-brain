from __future__ import annotations

import streamlit as st

from ott_brain.database import ensure_database
from ott_brain.movies import sync_movie_metadata
from ott_brain.tmdb import TmdbError, poster_url, search_movies

st.set_page_config(page_title="OTT Brain", page_icon="🎬", layout="wide")

ensure_database()


def render_home() -> None:
    st.header("Home")
    st.caption("What do you want to watch tonight?")
    st.text_area(
        "Ask in plain language (coming in Epic E4)",
        placeholder="e.g. dark psychological thriller under 2 hours",
        height=100,
        disabled=True,
        key="nl_query_placeholder",
    )
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
            cols = st.columns([1, 4, 1])
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
                        st.success(f"Saved {item.title} to your library.")
                    except TmdbError as exc:
                        st.error(str(exc))


def render_recommendations() -> None:
    st.header("Recommendations")
    st.info("Ranked picks arrive in Epic E6. Discovery pipeline lands in E4–E5.")


def render_history() -> None:
    st.header("History")
    st.info("Watch history UI ships in Epic E8. You can already save movies from Home search.")


def main() -> None:
    st.sidebar.title("OTT Brain")
    page = st.sidebar.radio(
        "Navigate",
        ["Home", "Recommendations", "History"],
        index=0,
    )
    st.sidebar.caption("Single-user · no login")

    if page == "Home":
        render_home()
    elif page == "Recommendations":
        render_recommendations()
    else:
        render_history()

    with st.sidebar.expander("Saved movies (debug)", expanded=False):
        # Lightweight confirmation that DB writes work without a full History screen.
        from ott_brain.database import connect

        with connect() as conn:
            rows = conn.execute(
                "SELECT tmdb_id, title, year FROM movies ORDER BY title LIMIT 20"
            ).fetchall()
        if not rows:
            st.caption("None yet — search and tap Save on Home.")
        else:
            for row in rows:
                st.text(f"{row['title']} ({row['year'] or '?'})")


if __name__ == "__main__":
    main()
