"""
AI4Kids - Admin "Codes" panel
Master key se login hone par dikhta hai.
"""

import io
import csv
import pandas as pd
import streamlit as st
from datetime import date

import device_lock as dl


def render():
    if not st.session_state.get("ai4k_admin"):
        st.error("Sirf admin ke liye.")
        return

    st.header("🔑 Access Codes")
    t1, t2, t3 = st.tabs(["Naye Codes", "Sab Codes", "Login Log"])

    with t1:
        c1, c2, c3 = st.columns(3)
        n = c1.number_input("Kitne codes?", 1, 500, 30)
        grade = c2.number_input("Grade", 1, 7, 5)
        exp = c3.date_input("Expiry", value=date(date.today().year, 12, 31))

        if st.button("Generate karein", type="primary"):
            codes = dl.generate_codes(int(n), int(grade), expires_on=str(exp))
            st.success(f"{len(codes)} codes ban gaye.")
            buf = io.StringIO()
            w = csv.writer(buf)
            w.writerow(["code", "grade", "expires_on"])
            for c in codes:
                w.writerow([c, grade, exp])
            st.download_button("📥 CSV download karein", buf.getvalue(),
                               file_name=f"ai4kids_codes_g{grade}_{date.today()}.csv",
                               mime="text/csv")
            st.code("\n".join(codes))

    with t2:
        sb = dl.get_sb()
        rows = (sb.table("access_codes")
                  .select("code,student_name,grade,status,claimed_at,"
                          "last_seen,reset_count,expires_on")
                  .order("created_at", desc=True).limit(1000).execute().data)
        if not rows:
            st.info("Abhi koi code nahi hai.")
        else:
            df = pd.DataFrame(rows)
            df["haalat"] = df["claimed_at"].apply(
                lambda x: "🔒 Device pe lock" if x else "🆓 Khali")

            f1, f2 = st.columns(2)
            g = f1.selectbox("Grade filter",
                             ["Sab"] + sorted(df["grade"].dropna().unique().tolist()))
            s = f2.selectbox("Haalat", ["Sab", "🔒 Device pe lock", "🆓 Khali"])
            view = df.copy()
            if g != "Sab":
                view = view[view["grade"] == g]
            if s != "Sab":
                view = view[view["haalat"] == s]

            st.dataframe(view, width='stretch', hide_index=True)
            st.caption(f"{len(view)} / {len(df)} codes")

            st.divider()
            st.subheader("Ek code pe amal")
            pick = st.selectbox("Code chunein", df["code"].tolist())
            a1, a2 = st.columns(2)
            if a1.button("🔄 Device Reset", width='stretch'):
                dl.reset_device(pick)
                st.success(f"{pick} ab kisi bhi device pe dobara register ho sakta hai.")
                st.rerun()
            if a2.button("🚫 Code Block", width='stretch'):
                dl.block_code(pick)
                st.warning(f"{pick} band kar diya gaya.")
                st.rerun()

    with t3:
        sb = dl.get_sb()
        logs = (sb.table("access_log").select("*")
                  .order("at", desc=True).limit(500).execute().data)
        if not logs:
            st.info("Abhi koi log nahi.")
        else:
            ldf = pd.DataFrame(logs)
            st.dataframe(ldf, width='stretch', hide_index=True)

            st.subheader("⚠️ Mushtaba codes (sharing ka shak)")
            bad = ldf[ldf["result"] == "WRONG_DEVICE"]
            if bad.empty:
                st.success("Koi sharing nazar nahi aa rahi.")
            else:
                counts = (bad.groupby("code").size()
                             .reset_index(name="ghalat_device_koshishein")
                             .sort_values("ghalat_device_koshishein", ascending=False))
                st.dataframe(counts, width='stretch', hide_index=True)
                st.caption("5 se zyada koshishein = code shayad share ho raha hai.")
