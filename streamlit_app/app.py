import streamlit as st
from supabase import create_client
from datetime import datetime

st.set_page_config(page_title="Learning Context", page_icon="📚", layout="centered")


@st.cache_resource
def get_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets.get("SUPABASE_ANON_KEY", st.secrets.get("SUPABASE_SERVICE_ROLE_KEY"))
    return create_client(url, key)


def load_context():
    client = get_supabase()
    result = client.table("learning_context").select("*").eq("id", 1).single().execute()
    return result.data


def save_context(data: dict):
    client = get_supabase()
    current = load_context()
    client.table("learning_context_history").insert({
        "snapshot": current,
    }).execute()
    data["updated_at"] = datetime.utcnow().isoformat()
    client.table("learning_context").update(data).eq("id", 1).execute()


def main():
    st.title("📚 Learning Context")
    st.caption("Configure what you want to learn. The AI uses this to score and curate your daily digest.")

    ctx = load_context()
    if not ctx:
        st.error("No learning context found. Run seed_context.py first.")
        return

    # --- Skill removal (outside the form) ---
    skill_levels = dict(ctx.get("skill_levels", {}))
    st.subheader("Current Skills")
    if skill_levels:
        for skill, level in list(skill_levels.items()):
            col_s, col_l, col_r = st.columns([3, 3, 1])
            with col_s:
                st.text(skill)
            with col_l:
                st.text(level)
            with col_r:
                if st.button("🗑️", key=f"remove_{skill}"):
                    del skill_levels[skill]
                    save_context({
                        "goals": ctx["goals"],
                        "digest_format": ctx["digest_format"],
                        "methodology": ctx["methodology"],
                        "skill_levels": skill_levels,
                        "time_availability": ctx["time_availability"],
                        "project_context": ctx["project_context"],
                    })
                    st.rerun()
    else:
        st.caption("No skills added yet.")

    st.divider()

    # --- Main form ---
    with st.form("learning_context_form"):
        st.subheader("Goals")
        goals = st.text_area(
            "What are you currently trying to learn?",
            value=ctx.get("goals", ""),
            height=120,
            placeholder="e.g., Building production ML systems, learning Rust for systems programming",
        )

        st.subheader("Methodology")
        methodology = ctx.get("methodology", {})
        col1, col2, col3 = st.columns(3)
        with col1:
            style = st.selectbox("Learning style", ["practical", "theoretical", "mixed"],
                                 index=["practical", "theoretical", "mixed"].index(methodology.get("style", "practical")))
        with col2:
            depth = st.selectbox("Depth", ["beginner", "intermediate", "advanced"],
                                 index=["beginner", "intermediate", "advanced"].index(methodology.get("depth", "intermediate")))
        with col3:
            consumption = st.text_input("Daily consumption time", value=methodology.get("consumption", "30min"))

        st.subheader("Add New Skill")
        col_ns, col_nl = st.columns(2)
        with col_ns:
            new_skill = st.text_input("Skill name", key="new_skill")
        with col_nl:
            new_level = st.selectbox("Level", ["beginner", "intermediate", "advanced"], key="new_level")

        st.subheader("Time & Context")
        time_availability = st.text_input("Time available for learning", value=ctx.get("time_availability", "30 minutes per day"))
        project_context = st.text_area(
            "Current project context",
            value=ctx.get("project_context", ""),
            height=100,
            placeholder="e.g., Building a SaaS product with Next.js + Python backend",
        )

        digest_format = st.selectbox("Digest format", ["daily", "weekly"],
                                     index=["daily", "weekly"].index(ctx.get("digest_format", "daily")))

        submitted = st.form_submit_button("💾 Save Learning Context", type="primary", use_container_width=True)

        if submitted:
            updated_skills = dict(skill_levels)
            if new_skill.strip():
                updated_skills[new_skill.strip()] = new_level

            save_context({
                "goals": goals,
                "digest_format": digest_format,
                "methodology": {"style": style, "depth": depth, "consumption": consumption},
                "skill_levels": updated_skills,
                "time_availability": time_availability,
                "project_context": project_context,
            })
            st.success("Learning context saved!")
            st.rerun()

    # --- Digest history ---
    st.divider()
    st.subheader("📊 Recent Digests")
    client = get_supabase()
    logs = client.table("digest_log").select("*").order("digest_date", desc=True).limit(7).execute()
    if logs.data:
        for log in logs.data:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Date", log["digest_date"])
            with col2:
                st.metric("Items", log.get("items_emailed", 0))
            with col3:
                precision = log.get("precision_rate")
                st.metric("Precision", f"{precision}%" if precision else "N/A")
            with col4:
                st.metric("Status", log.get("status", "unknown"))
    else:
        st.info("No digest history yet. The first digest will run at 6 AM UTC.")


if __name__ == "__main__":
    main()
