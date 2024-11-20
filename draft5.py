import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import random  # For lucky draw
from PIL import Image  # For image handling
import os


def analyze_guesses(guesses_df, correct_answers):
    detailed_results = []

    for _, row in guesses_df.iterrows():
        participant_name = row["Name"]
        # Process races (Race2 to Race7)
        for race_num in range(2, 8):
            actual_1st = str(correct_answers.get(f"Race{race_num}_1st", "0")).strip()
            actual_2nd = str(correct_answers.get(f"Race{race_num}_2nd", "0")).strip()
            actual_3rd = str(correct_answers.get(f"Race{race_num}_3rd", "0")).strip()

            if actual_1st == "0" and actual_2nd == "0" and actual_3rd == "0":
                continue

            participant_1st = str(row.get(f"Race{race_num}_1st", "0")).strip()
            participant_2nd = str(row.get(f"Race{race_num}_2nd", "0")).strip()
            participant_3rd = str(row.get(f"Race{race_num}_3rd", "0")).strip()

            points = 0
            if participant_1st == actual_1st:
                points += 12
            if participant_2nd == actual_2nd:
                points += 6
            if participant_3rd == actual_3rd:
                points += 2

            detailed_results.append({
                "Name": participant_name,
                "Race": f"Race {race_num}",
                "1st Place Guess": participant_1st,
                "1st Place Actual": actual_1st,
                "1st Place Correct": participant_1st == actual_1st,
                "2nd Place Guess": participant_2nd,
                "2nd Place Actual": actual_2nd,
                "2nd Place Correct": participant_2nd == actual_2nd,
                "3rd Place Guess": participant_3rd,
                "3rd Place Actual": actual_3rd,
                "3rd Place Correct": participant_3rd == actual_3rd,
                "Points": points
            })

        # Process Opt Six (OPT2 to OPT7)
        opt_actual = [str(correct_answers.get(f"OPT{i}", "0")).strip() for i in range(2, 8)]
        if any(value != "0" for value in opt_actual):
            participant_opt_guesses = [str(row.get(f"OPT{i}", "0")).strip() for i in range(2, 8)]
            for idx, opt_num in enumerate(range(2, 8)):
                actual = opt_actual[idx]
                guess = participant_opt_guesses[idx]
                if actual == "0":
                    continue  # Skip if actual is 0
                is_correct = guess == actual
                points = 1 if is_correct else 0
                detailed_results.append({
                    "Name": participant_name,
                    "Race": f"OPT{opt_num}",
                    "1st Place Guess": guess,
                    "1st Place Actual": actual,
                    "1st Place Correct": is_correct,
                    "2nd Place Guess": "",
                    "2nd Place Actual": "",
                    "2nd Place Correct": False,
                    "3rd Place Guess": "",
                    "3rd Place Actual": "",
                    "3rd Place Correct": False,
                    "Points": points
                })

    return pd.DataFrame(detailed_results)

def create_pdf(filtered_df, correct_summary, top_scorers_dict, lucky_draw_winners):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Title
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, "Race Guess Analyzer - Detailed Report")

    y_position = height - 80

    # Summary Section
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y_position, "Summary of Participant Performance:")
    y_position -= 20

    p.setFont("Helvetica", 10)
    for _, row in correct_summary.iterrows():
        summary_text = f"{row['Name']}: {row['Points']} Points | 1st Place Correct: {int(row['1st Place Correct'])} | " \
                       f"2nd Place Correct: {int(row['2nd Place Correct'])} | 3rd Place Correct: {int(row['3rd Place Correct'])}"
        p.drawString(50, y_position, summary_text)
        y_position -= 15
        if y_position < 50:
            p.showPage()
            y_position = height - 50

    # Top Scorer Section
    if top_scorers_dict:
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y_position - 10, "Top Performers:")
        y_position -= 30
        p.setFont("Helvetica", 10)
        for category, scorers in top_scorers_dict.items():
            p.drawString(50, y_position, f"{category}:")
            y_position -= 15
            for scorer in scorers:
                p.drawString(70, y_position, f"- {scorer}")
                y_position -= 15
                if y_position < 50:
                    p.showPage()
                    y_position = height - 50

    # Lucky Draw Winners
    if lucky_draw_winners:
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y_position - 10, "Lucky Draw Winners:")
        y_position -= 30
        p.setFont("Helvetica", 10)
        for category, winner in lucky_draw_winners.items():
            p.drawString(50, y_position, f"{category}: {winner}")
            y_position -= 15
            if y_position < 50:
                p.showPage()
                y_position = height - 50

    # Detailed Results Section
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y_position - 10, "Detailed Results:")
    y_position -= 30

    headers = list(filtered_df.columns)
    line_height = 15

    # Print headers
    for i, header in enumerate(headers):
        p.drawString(50 + i * 100, y_position, header)
    y_position -= line_height

    # Print rows
    for _, row in filtered_df.iterrows():
        for i, value in enumerate(row):
            p.drawString(50 + i * 100, y_position, str(value))
        y_position -= line_height
        if y_position < 50:
            p.showPage()
            y_position = height - 50

    p.save()
    buffer.seek(0)
    return buffer

def create_header_with_logo():
    # Custom CSS for high-quality image rendering
    st.markdown("""
        <style>
        [data-testid="stImage"] {
            margin-bottom: -2rem;
        }
        [data-testid="stImage"] > img {
            border-radius: 10px;
            image-rendering: -webkit-optimize-contrast;  /* For Chrome */
            image-rendering: crisp-edges;  /* For Firefox */
            -ms-interpolation-mode: nearest-neighbor;  /* For IE */
            max-width: none;  /* Prevents automatic scaling */
        }
        </style>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 4])
    with col1:
        try:
            # Open and process the image with PIL

            base_dir = os.path.dirname(os.path.abspath(__file__))
            logo_path = os.path.join(base_dir, 'pic.png')
            image = Image.open(logo_path)
            
            # If the image is not in RGBA/RGB format, convert it
            if image.mode not in ('RGBA', 'RGB'):
                image = image.convert('RGBA')
            
            # Calculate the display size while maintaining aspect ratio
            original_width, original_height = image.size
            target_width = 300  # Desired width
            aspect_ratio = original_height / original_width
            target_height = int(target_width * aspect_ratio)
            
            # Resize using high-quality resampling
            image = image.resize((target_width, target_height), Image.Resampling.LANCZOS)
            
            # Display the processed image
            st.image(image, 
                    use_column_width=False,
                    width=target_width,
                    output_format='PNG',  # Force PNG format for better quality
                    clamp=False)  # Prevent color clamping
            
        except Exception as e:
            st.error(f"Error loading logo: {str(e)}")
            
    with col2:
        st.title("")
        st.write("")


def add_sidebar_logo():
    # Custom CSS to style the sidebar header
    st.markdown("""
        <style>
        .sidebar-logo {
            margin-top: -60px;  /* Adjust this value to fine-tune vertical position */
            margin-bottom: 20px;
            padding: 0;
            text-align: center;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Create a container for the logo above the sidebar
    with st.sidebar:
        st.markdown('<div class="sidebar-logo">', unsafe_allow_html=True)
        try:
            # Open and process the image with PIL
            image = Image.open('pic2.png')
            
            # Convert image to RGBA if needed
            if image.mode not in ('RGBA', 'RGB'):
                image = image.convert('RGBA')
            
            # Calculate dimensions while maintaining aspect ratio
            target_width = 200  # Adjust this value to match your sidebar width
            aspect_ratio = image.height / image.width
            target_height = int(target_width * aspect_ratio)
            
            # Resize image
            image = image.resize((target_width, target_height), Image.Resampling.LANCZOS)
            
            # Display the image
            st.image(image, 
                    use_column_width=True,
                    output_format='PNG')
            
        except Exception as e:
            st.error(f"Error loading sidebar logo: {str(e)}")
        st.markdown('</div>', unsafe_allow_html=True)

# Initialize session state for lucky draw winners as a dictionary
if 'lucky_draw_winners' not in st.session_state:
    st.session_state.lucky_draw_winners = {}

# Streamlit app layout with custom styling
st.set_page_config(page_title="AESGC Race Predictor Pro",
                   page_icon="🏇",
                   layout="wide",
                   initial_sidebar_state="expanded")

# Enhanced Custom CSS for styling including logo
st.markdown("""
    <style>
    .race-container {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    .stButton button {
        width: 100%;
    }
    .header-container {
        display: flex;
        align-items: center;
        padding: 1rem 0;
        margin-bottom: 2rem;
        background-color: white;
        border-bottom: 1px solid #e6e6e6;
    }
    /* Improved image quality settings */
    img {
        backface-visibility: hidden;
        transform: translateZ(0);
        -webkit-font-smoothing: subpixel-antialiased;
    }
    </style>
""", unsafe_allow_html=True)

# Call functions to create headers and logos
create_header_with_logo()
add_sidebar_logo()

st.title("🏇 AESGC Race Predictor Pro")
st.write("Upload the participant guesses file and enter the correct answers to analyze results.")

# Sidebar for file upload and race inputs
with st.sidebar:
    guesses_file = st.file_uploader("", type=["csv"])

    st.header("Enter Correct Answers")
    correct_answers = {}
    valid_race_count = 0
    MAX_POINTS_PER_RACE = 21
    TOTAL_RACES = 6
    MAX_TOTAL_POINTS = MAX_POINTS_PER_RACE * TOTAL_RACES

    # Color palette for race containers
    colors = ['#ffecec', '#ecffec', '#ecebff', '#fff6ec', '#f6ecff', '#ecfff6']

    for race_num in range(2, 8):
        # Create a unique container for each race with different styling
        with st.container():
            st.markdown(f"""
                <div style="
                    background-color: {colors[(race_num-2)%len(colors)]};
                    padding: 15px;
                    border-radius: 10px;
                    margin: 10px 0;
                    border: 1px solid rgba(49, 51, 63, 0.2);
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                ">
                    <h3 style="color: #333; margin-bottom: 10px; font-size: 1.1em;">Race {race_num}</h3>
                </div>
                """, unsafe_allow_html=True)

            col1, col2, col3 = st.columns(3)

            with col1:
                correct_answers[f"Race{race_num}_1st"] = st.text_input(
                    "1st",
                    value="0",
                    key=f"first_{race_num}",
                    help=f"Enter horse number for 1st place in Race {race_num}"
                )

            with col2:
                correct_answers[f"Race{race_num}_2nd"] = st.text_input(
                    "2nd",
                    value="0",
                    key=f"second_{race_num}",
                    help=f"Enter horse number for 2nd place in Race {race_num}"
                )

            with col3:
                correct_answers[f"Race{race_num}_3rd"] = st.text_input(
                    "3rd",
                    value="0",
                    key=f"third_{race_num}",
                    help=f"Enter horse number for 3rd place in Race {race_num}"
                )

            if (correct_answers[f"Race{race_num}_1st"] != "0" or
                correct_answers[f"Race{race_num}_2nd"] != "0" or
                correct_answers[f"Race{race_num}_3rd"] != "0"):
                valid_race_count += 1

    # Input for Opt Six (OPT2 to OPT7)
    with st.container():
        st.markdown(f"""
            <div style="
                background-color: {colors[0]};
                padding: 15px;
                border-radius: 10px;
                margin: 10px 0;
                border: 1px solid rgba(49, 51, 63, 0.2);
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            ">
                <h3 style="color: #333; margin-bottom: 10px; font-size: 1.1em;">Opt Six</h3>
            </div>
            """, unsafe_allow_html=True)

        opt_cols = st.columns(6)
        for idx, i in enumerate(range(2, 8)):
            with opt_cols[idx]:
                correct_answers[f"OPT{i}"] = st.text_input(
                    f"OPT{i}",
                    value="0",
                    key=f"opt_{i}",
                    help=f"Enter correct value for OPT{i}"
                )

    # Update valid_race_count
    opt_values = [correct_answers[f"OPT{i}"] for i in range(2, 8)]
    if any(value != "0" for value in opt_values):
        valid_race_count += 1
        MAX_TOTAL_POINTS += 6  # 1 point per correct Opt Six guess


if valid_race_count == 0:
    st.warning("No valid race results entered. Please input at least one non-zero value for any race or Opt Six.")
else:
    if guesses_file:
        guesses_df = pd.read_csv(guesses_file)
        detailed_results_df = analyze_guesses(guesses_df, correct_answers)

        with st.container():
            st.subheader("Detailed Results")
            st.dataframe(detailed_results_df[["Name", "Points"]])

            st.divider()

        # Summarize Performance
        correct_summary = (
            detailed_results_df
            .groupby("Name")[["1st Place Correct", "2nd Place Correct", "3rd Place Correct", "Points"]]
            .sum()
            .reset_index()
        )

       # Track all previous lucky draw winners globally
        if 'all_lucky_draw_winners' not in st.session_state:
            st.session_state.all_lucky_draw_winners = set()

        # Apply filtered conditions for top performers
        # For Race 2 and Race 3 combined, participants with score >=28
        race_2_3_df = detailed_results_df[
            detailed_results_df['Race'].isin(['Race 2', 'Race 3'])
        ]
        race_2_3_points = race_2_3_df.groupby('Name')['Points'].sum().reset_index()
        race_2_3_top = race_2_3_points[
            (race_2_3_points['Points'] >= 28) & 
            (~race_2_3_points['Name'].isin(st.session_state.all_lucky_draw_winners))
        ]['Name']

        # For Opt Six, participants with score >=3
        opt_six_df = detailed_results_df[
            detailed_results_df['Race'].str.startswith('OPT')
        ]
        opt_six_points = opt_six_df.groupby('Name')['Points'].sum().reset_index()
        opt_six_top = opt_six_points[
            (opt_six_points['Points'] >= 3) & 
            (~opt_six_points['Name'].isin(st.session_state.all_lucky_draw_winners))
        ]['Name']

        # For Races 4-7, identify participants with highest total points
        races_4_7_df = detailed_results_df[
            detailed_results_df['Race'].isin(['Race 4', 'Race 5', 'Race 6', 'Race 7'])
        ]
        races_4_7_points = races_4_7_df.groupby('Name')['Points'].sum().reset_index()
        max_points_races_4_7 = races_4_7_points['Points'].max()
        races_4_7_top = races_4_7_points[
            (races_4_7_points['Points'] == max_points_races_4_7) & 
            (~races_4_7_points['Name'].isin(st.session_state.all_lucky_draw_winners))
        ]['Name']

        # Prepare top_scorers dictionary
        top_scorers_dict = {}
        if not race_2_3_top.empty:
            top_scorers_dict['Races 2 & 3'] = race_2_3_top.tolist()
        if not opt_six_top.empty:
            top_scorers_dict['Opt Six'] = opt_six_top.tolist()
        if not races_4_7_top.empty:
            top_scorers_dict['Races 4-7'] = races_4_7_top.tolist()

        # Display Top Performers
        st.subheader("Top Performers")

        # For Races 2 & 3
        if 'Races 2 & 3' in top_scorers_dict:
            st.write("**Top Performers for Races 2 & 3**")
            st.success("Participants who scored >=28 points in Races 2 & 3:")
            for name in top_scorers_dict['Races 2 & 3']:
                st.write(f"- {name}")
            # Lucky Draw if multiple top scorers
            if len(top_scorers_dict['Races 2 & 3']) > 1:
                if st.button("Conduct Lucky Draw for Races 2 & 3"):
                    winner = random.choice(top_scorers_dict['Races 2 & 3'])
                    st.session_state.lucky_draw_winners['Races 2 & 3'] = winner
                    st.session_state.all_lucky_draw_winners.add(winner)
                if 'Races 2 & 3' in st.session_state.lucky_draw_winners:
                    st.info(f"Lucky Draw Winner for Races 2 & 3: {st.session_state.lucky_draw_winners['Races 2 & 3']}")
            elif len(top_scorers_dict['Races 2 & 3']) == 1:
                st.success(f"Single Winner for Races 2 & 3: {top_scorers_dict['Races 2 & 3'][0]}")

        # For Opt Six
        if 'Opt Six' in top_scorers_dict:
            st.write("**Top Performers for Opt Six**")
            st.success("Participants who scored >=3 points in Opt Six:")
            for name in top_scorers_dict['Opt Six']:
                st.write(f"- {name}")
            # Lucky Draw if multiple top scorers
            if len(top_scorers_dict['Opt Six']) > 1:
                if st.button("Conduct Lucky Draw for Opt Six"):
                    winner = random.choice(top_scorers_dict['Opt Six'])
                    st.session_state.lucky_draw_winners['Opt Six'] = winner
                    st.session_state.all_lucky_draw_winners.add(winner)
                if 'Opt Six' in st.session_state.lucky_draw_winners:
                    st.info(f"Lucky Draw Winner for Opt Six: {st.session_state.lucky_draw_winners['Opt Six']}")
            elif len(top_scorers_dict['Opt Six']) == 1:
                st.success(f"Single Winner for Opt Six: {top_scorers_dict['Opt Six'][0]}")

        # For Races 4-7
        if 'Races 4-7' in top_scorers_dict:
            st.write("**Top Performers for Races 4-7**")
            st.success("Participants with the highest points in Races 4-7:")
            for name in top_scorers_dict['Races 4-7']:
                st.write(f"- {name}")
            # Lucky Draw if multiple top scorers
            if len(top_scorers_dict['Races 4-7']) > 1:
                if st.button("Conduct Lucky Draw for Races 4-7"):
                    winner = random.choice(top_scorers_dict['Races 4-7'])
                    st.session_state.lucky_draw_winners['Races 4-7'] = winner
                    st.session_state.all_lucky_draw_winners.add(winner)
                if 'Races 4-7' in st.session_state.lucky_draw_winners:
                    st.info(f"Lucky Draw Winner for Races 4-7: {st.session_state.lucky_draw_winners['Races 4-7']}")
            elif len(top_scorers_dict['Races 4-7']) == 1:
                st.success(f"Single Winner for Races 4-7: {top_scorers_dict['Races 4-7'][0]}")

        st.divider()

        # Analyze Specific Participant
        st.subheader("Analyze Specific Participant")
        participant_names = detailed_results_df["Name"].unique()
        selected_participant = st.selectbox("Select a Participant", options=participant_names)

        participant_results = detailed_results_df[detailed_results_df["Name"] == selected_participant]
        if not participant_results.empty:
            total_correct = participant_results[["1st Place Correct", "2nd Place Correct", "3rd Place Correct"]].sum().sum()
            if total_correct == 0:
                st.warning(f"{selected_participant} had no correct guesses.")
            else:
                st.dataframe(participant_results)

                st.divider()

                # Gauge Chart for Total Points
                st.subheader(f"Total Points for {selected_participant}")
                total_points = participant_results["Points"].sum()
                fig_points = go.Figure(go.Indicator(
                    mode="number+gauge",
                    value=total_points,
                    title={"text": "Total Points"},
                    gauge={"axis": {"range": [0, MAX_TOTAL_POINTS]}},
                ))
                st.plotly_chart(fig_points)

        # Provide option to download detailed results as a PDF
        st.divider()
        st.subheader("Download Results")
        pdf_buffer = create_pdf(
            detailed_results_df,  # Use the full detailed results
            correct_summary,
            top_scorers_dict,
            st.session_state.lucky_draw_winners
        )
        st.download_button(
            label="Download Detailed Results as PDF",
            data=pdf_buffer,
            file_name="detailed_results.pdf",
            mime="application/pdf",
        )
