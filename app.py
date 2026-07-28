import streamlit as st
import preprocessor, helper
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Set page layout to wide
st.set_page_config(page_title="WhatsApp Chat Analyzer", layout="wide")

# 2. Inject Custom CSS for Dark Theme & Compact Metric Cards
st.markdown("""
<style>
    .stApp {
        background-color: #0E1117 !important;
        color: #FAFAFA !important;
    }
    section[data-testid="stSidebar"] {
        background-color: #161B22 !important;
        color: #FAFAFA !important;
    }
    h1, h2, h3, h4, h5, h6, p, label, .stMarkdown {
        color: #FAFAFA !important;
    }
    .dataframe {
        background-color: #161B22 !important;
        color: #FAFAFA !important;
    }
    /* Sleek dashboard card styling for top statistics */
    div[data-testid="metric-container"] {
        background-color: #1F2428;
        border: 1px solid #30363D;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# 3. Configure Matplotlib Global Style & Prevent Giant "Zoomed-in" Fonts
plt.style.use('dark_background')
plt.rcParams.update({
    'font.size': 10,
    'axes.labelsize': 10,
    'axes.titlesize': 12,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'figure.titlesize': 14,
    'figure.autolayout': True
})

st.sidebar.title("Whatsapp Chat Analyzer")

uploaded_file = st.sidebar.file_uploader("Choose a file")
if uploaded_file is not None:
    bytes_data = uploaded_file.getvalue()
    
    # Safely decode text files across different OS encodings
    try:
        data = bytes_data.decode("utf-8")
    except UnicodeDecodeError:
        try:
            data = bytes_data.decode("utf-16")
        except UnicodeDecodeError:
            data = bytes_data.decode("latin-1", errors="ignore")
        
    df = preprocessor.preprocess(data)

    if df.empty:
        st.error("Could not parse timestamps in this file. Please verify it is a valid WhatsApp chat export.")
    else:
        # Fetch unique users
        user_list = df['user'].unique().tolist()
        
        if 'group_notification' in user_list:
            user_list.remove('group_notification')
            
        user_list.sort()
        user_list.insert(0, "Overall")

        selected_user = st.sidebar.selectbox("Show analysis wrt", user_list)

        if st.sidebar.button("Show Analysis"):

            # --- TOP STATISTICS AREA (Using st.metric instead of st.title) ---
            num_messages, words, num_media_messages, num_links = helper.fetch_stats(selected_user, df)
            st.title("Top Statistics")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(label="Total Messages", value=f"{num_messages:,}")
            with col2:
                st.metric(label="Total Words", value=f"{words:,}")
            with col3:
                st.metric(label="Media Shared", value=f"{num_media_messages:,}")
            with col4:
                st.metric(label="Links Shared", value=f"{num_links:,}")

            st.markdown("---")

            # --- MONTHLY TIMELINE (Widescreen 12x3.5 ratio prevents vertical ballooning) ---
            st.subheader("Monthly Timeline")
            timeline = helper.monthly_timeline(selected_user, df)
            fig, ax = plt.subplots(figsize=(12, 3.5))
            ax.plot(timeline['time'], timeline['message'], color='#00FF66', linewidth=2)
            plt.xticks(rotation=45, ha='right')
            ax.grid(True, linestyle='--', alpha=0.2)
            st.pyplot(fig, use_container_width=True)

            # --- DAILY TIMELINE ---
            st.subheader("Daily Timeline")
            daily_timeline = helper.daily_timeline(selected_user, df)
            fig, ax = plt.subplots(figsize=(12, 3.5))
            ax.plot(daily_timeline['only_date'], daily_timeline['message'], color='#00E5FF', linewidth=1.5)
            plt.xticks(rotation=45, ha='right')
            ax.grid(True, linestyle='--', alpha=0.2)
            st.pyplot(fig, use_container_width=True)

            st.markdown("---")

            # --- ACTIVITY MAP ---
            st.subheader('Activity Map')
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Most Busy Day**")
                busy_day = helper.week_activity_map(selected_user, df)
                fig, ax = plt.subplots(figsize=(7, 4))
                ax.bar(busy_day.index, busy_day.values, color='#E040FB', width=0.6)
                plt.xticks(rotation=45, ha='right')
                ax.grid(axis='y', linestyle='--', alpha=0.2)
                st.pyplot(fig, use_container_width=True)

            with col2:
                st.markdown("**Most Busy Month**")
                busy_month = helper.month_activity_map(selected_user, df)
                fig, ax = plt.subplots(figsize=(7, 4))
                ax.bar(busy_month.index, busy_month.values, color='#FFAB00', width=0.6)
                plt.xticks(rotation=45, ha='right')
                ax.grid(axis='y', linestyle='--', alpha=0.2)
                st.pyplot(fig, use_container_width=True)

            # --- WEEKLY ACTIVITY HEATMAP ---
            st.subheader("Weekly Activity Map")
            user_heatmap = helper.activity_heatmap(selected_user, df)
            if not user_heatmap.empty:
                fig, ax = plt.subplots(figsize=(12, 4))
                sns.heatmap(user_heatmap, ax=ax, cmap="viridis", cbar_kws={'label': 'Message Count'}, linewidths=0.5)
                st.pyplot(fig, use_container_width=True)
            else:
                st.info("Not enough data to generate a weekly heatmap.")

            st.markdown("---")

            # --- GROUP LEVEL: BUSIEST USERS ---
            if selected_user == 'Overall':
                st.subheader('Most Busy Users')
                x, new_df = helper.most_busy_users(df)
                
                col1, col2 = st.columns([3, 2])

                with col1:
                    fig, ax = plt.subplots(figsize=(8, 4))
                    ax.bar(x.index, x.values, color='#FF5252', width=0.6)
                    plt.xticks(rotation=45, ha='right')
                    ax.grid(axis='y', linestyle='--', alpha=0.2)
                    st.pyplot(fig, use_container_width=True)
                with col2:
                    st.dataframe(new_df, use_container_width=True, height=250)

                st.markdown("---")

            # --- WORDCLOUD ---
            st.subheader("Wordcloud")
            df_wc = helper.create_wordcloud(selected_user, df)
            fig, ax = plt.subplots(figsize=(10, 4.5))
            ax.imshow(df_wc, interpolation='bilinear')
            ax.axis("off")
            st.pyplot(fig, use_container_width=True)

            st.markdown("---")

            # --- MOST COMMON WORDS ---
            st.subheader('Most Common Words')
            most_common_df = helper.most_common_words(selected_user, df)
            if not most_common_df.empty:
                fig, ax = plt.subplots(figsize=(10, 5))
                # Sort ascending so the largest horizontal bar appears at the top of the chart
                most_common_df = most_common_df.sort_values(by=1, ascending=True)
                ax.barh(most_common_df[0], most_common_df[1], color='#18FFFF', height=0.6)
                ax.grid(axis='x', linestyle='--', alpha=0.2)
                st.pyplot(fig, use_container_width=True)
            else:
                st.info("Not enough data to display most common words.")

            st.markdown("---")

            # --- EMOJI ANALYSIS ---
            st.subheader("Emoji Analysis")
            emoji_df = helper.emoji_helper(selected_user, df)

            col1, col2 = st.columns([2, 3])

            with col1:
                st.dataframe(emoji_df, use_container_width=True, height=300)
            with col2:
                if not emoji_df.empty:
                    fig, ax = plt.subplots(figsize=(6, 5))
                    ax.pie(
                        emoji_df[1].head(), 
                        labels=emoji_df[0].head(), 
                        autopct="%0.2f%%", 
                        textprops={'color': "w", 'fontsize': 11},
                        startangle=140,
                        wedgeprops={'edgecolor': '#0E1117', 'linewidth': 1.5}
                    )
                    ax.axis('equal')  # Keeps pie chart perfectly circular
                    st.pyplot(fig, use_container_width=True)
                else:
                    st.info("No emojis found for this selection.")