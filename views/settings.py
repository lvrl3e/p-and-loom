import streamlit as st

from ui import theme

st.markdown(theme.page_header("Settings", "Customize how P&Loom looks", icon="settings"), unsafe_allow_html=True)

MODE_LABELS = {"Auto": None, "Light": "light", "Dark": "dark"}
MODE_LABELS_REVERSED = {v: k for k, v in MODE_LABELS.items()}

with st.container(key="card-appearance-settings"):
    st.markdown(
        theme.card_header("Appearance", "Light and dark auto-detect per browser — override it here if that's unreliable", icon="moon"),
        unsafe_allow_html=True,
    )

    current_override = theme.get_mode_override()
    current_mode_label = MODE_LABELS_REVERSED[current_override]

    mode_choice = st.segmented_control(
        "Mode", list(MODE_LABELS.keys()), default=current_mode_label, key="appearance_mode_widget",
    )
    if mode_choice and MODE_LABELS[mode_choice] != current_override:
        theme.set_mode_override(MODE_LABELS[mode_choice])
        st.rerun()

st.write("")

current_accent = theme.get_custom_accent() or theme.DEFAULT_ACCENT

with st.container(key="card-accent-settings"):
    st.markdown(
        theme.card_header("Accent Color", "Used for buttons, highlights, and charts throughout the app", icon="pulse"),
        unsafe_allow_html=True,
    )

    preset_cols = st.columns(len(theme.ACCENT_PRESETS))
    for col, preset in zip(preset_cols, theme.ACCENT_PRESETS):
        with col:
            if st.button(" ", key=f"preset-{preset.lstrip('#')}", width="stretch", help=preset):
                theme.set_custom_accent(preset)
                st.rerun()

    st.write("")
    picker_col, save_col = st.columns([2, 1])
    with picker_col:
        picked = st.color_picker("Custom color", value=current_accent, label_visibility="collapsed")
    with save_col:
        if st.button("Save Color", type="primary", width="stretch"):
            theme.set_custom_accent(picked)
            st.rerun()

    if theme.get_custom_accent():
        st.write("")
        if st.button("Reset to Default", type="secondary"):
            theme.set_custom_accent(None)
            st.rerun()
