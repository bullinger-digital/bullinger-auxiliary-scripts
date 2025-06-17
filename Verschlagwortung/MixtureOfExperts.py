import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import argparse

argparser = argparse.ArgumentParser(description="Process topic assignments from two models.")
argparser.add_argument("--gpt_file", '-gpt', type=str, help="Path to a csv file with GPT-4o model annotations.")
argparser.add_argument("--deepseek_file", '-ds', type=str, help="Path to a csv file with DeepSeek model annotations.")
argparser.add_argument("--output_file", '-o', type=str, help="Path to a csv file that saves the merged topics IDs.")
argparser.add_argument("--mapping_file", '-m', type=str, default="topic_mapping.csv", help="Path to save the topic mapping file.")
argparser.add_argument("--plot_file", '-p', type=str, help="Path to save the stacked bar plot image.")

args = argparser.parse_args()

# Plot style
sns.set(style="whitegrid")

# Topics and thresholds
topics = [
    "Everyday Life", "Requests and Petitions", "Education System",
    "Books, Printing, and Publishing", "Faith and Doctrine in Practice",
    "Faith and Doctrine in Theory", "Disasters and Natural Phenomena",
    "Illness, Death, and Recovery in Society", "Illness, Death, and Recovery among Family and Close Friends",
    "Military and Political Affairs", "Religious Persecution and Martyrdom"
]

topics_dict = {
    "Everyday Life": "Alltag",
    "Requests and Petitions": "Anfragen und Bitten",
    "Education System": "Bildungswesen",
    "Books, Printing, and Publishing": "Bücher, Druck und Verlagswesen",
    "Faith and Doctrine in Practice": "Glaube und Lehre in der Praxis",
    "Faith and Doctrine in Theory": "Glaube und Lehre in der Theorie",
    "Disasters and Natural Phenomena": "Katastrophen und Naturphänomen",
    "Illness, Death, and Recovery in Society": "Krankheit, Tod und Genesung in der Gesellschaft",
    "Illness, Death, and Recovery among Family and Close Friends": "Krankheit, Tod und Genesung innerhalb der Familie und enger Freunde",
    "Military and Political Affairs": "Militärische und politische Angelegenheiten",
    "Religious Persecution and Martyrdom": "Religiöse Verfolgung und Märtyrertum"
}

thresholds = {
    "Requests and Petitions": 90,
    "Military and Political Affairs": 90
}

# Assign topic numbers
topic_number_map = {topic: idx + 1 for idx, topic in enumerate(topics)}

# Save mapping file
mapping_df = pd.DataFrame([
    {"Topic Number": topic_number_map[topic], "Topic (DE)": topics_dict[topic], "Topic (EN)": topic}
    for topic in topics
])
mapping_df.to_csv(args.mapping_file, index=False, encoding='utf-8')

# Load data
df1 = pd.read_csv(args.gpt_file, encoding='utf-8')
df2 = pd.read_csv(args.deepseek_file, encoding='utf-8')
merged_df = pd.merge(df1, df2, on="File ID", suffixes=('_gpt-4o', '_deepseek'))

# Tracking
processed_rows_ids = []
file_with_no_topics = []

# Stats trackers
model1_topic_counts = {t: 0 for t in topics}
model2_topic_counts = {t: 0 for t in topics}
both_topic_counts = {t: 0 for t in topics}
agreement_counts = {t: 0 for t in topics}

# Per-file topic counts
topic_counts_model1 = []
topic_counts_model2 = []
topic_counts_both = []

# Main loop
for _, row in merged_df.iterrows():
    file_id = int(row['File ID'])
    selected_topic_ids = []
    count1 = 0
    count2 = 0

    for topic in topics:
        col_model1 = topic + '_gpt-4o'
        col_model2 = topic + '_deepseek'
        threshold = thresholds.get(topic, 60)

        val1 = float(row[col_model1])
        val2 = float(row[col_model2])

        if topic in ["Requests and Petitions", "Military and Political Affairs"]:
            if val1 >= threshold and val2 >= threshold:
                selected_topic_ids.append(topic_number_map[topic])
                both_topic_counts[topic] += 1
                agreement_counts[topic] += 1
        else:
            if (val1 >= threshold and val2 >= 20) or (val2 >= threshold and val1 >= 20):
                selected_topic_ids.append(topic_number_map[topic])
                if val1 >= threshold and val2 >= threshold:
                    both_topic_counts[topic] += 1
                    agreement_counts[topic] += 1

        if val1 >= threshold:
            model1_topic_counts[topic] += 1
            count1 += 1
        if val2 >= threshold:
            model2_topic_counts[topic] += 1
            count2 += 1

    # Store per-file counts
    topic_counts_model1.append(count1)
    topic_counts_model2.append(count2)
    topic_counts_both.append(len(selected_topic_ids))

    if not selected_topic_ids:
        file_with_no_topics.append(file_id)

    processed_rows_ids.append([file_id, selected_topic_ids])

# Save file with topic IDs only
df_ids = pd.DataFrame(processed_rows_ids, columns=['File ID', 'Topics'])
df_ids.to_csv(args.output_file, index=False, encoding='utf-8')

print("✅ Topic ID mapping saved to: topic_mapping.csv")
print("✅ Topic ID list per file saved to: merged_topics_ids.csv")

# 📌 Explanation of topic assignment logic and thresholds
print("\nTopic Assignment Logic Summary:\n")
print("- 🔒 STRICT INTERSECTION: Assigned only if BOTH models ≥ 90. Topics like 'Requests and Petitions' and 'Military and Political Affairs' are strongly present in the correspondance, therefore we used the Intersection logic to avoid false positives and over-representation.\n")
print("- 🔄 FLEXIBLE UNION: Assigned if ONE model ≥ 60 and the OTHER ≥ 20. All other topics were assigned based on the flexible union logic.\n")

# Stacked Bar Plot for Files Assigned by Both Models for Each Topic

# Calculate the number of files assigned by each model (separately and together)
assigned_by_gpt_only = {t: 0 for t in topics}
assigned_by_deepseek_only = {t: 0 for t in topics}
assigned_by_both = {t: 0 for t in topics}

for i, file_id in enumerate(merged_df["File ID"]):
    for topic in topics:
        col_model1 = topic + '_gpt-4o'
        col_model2 = topic + '_deepseek'

        # Get assignment status for both models
        val1 = float(merged_df.at[i, col_model1])
        val2 = float(merged_df.at[i, col_model2])

        # Count assignments for each model
        if val1 >= thresholds.get(topic, 60) and val2 >= thresholds.get(topic, 60):
            assigned_by_both[topic] += 1
        elif val1 >= thresholds.get(topic, 60):
            assigned_by_gpt_only[topic] += 1
        elif val2 >= thresholds.get(topic, 60):
            assigned_by_deepseek_only[topic] += 1

# Prepare the data for stacked bar plot
gpt_only_values = [assigned_by_gpt_only[t] for t in topics]
deepseek_only_values = [assigned_by_deepseek_only[t] for t in topics]
both_values = [assigned_by_both[t] for t in topics]

# create a plot if arguments are provided
if args.plot_file:

    # Create stacked bar plot
    plt.figure(figsize=(10, 6))
    bar_width = 0.6

    # Plot 'both' as base, then GPT-only, then Deepseek-only
    plt.barh([topics_dict[t] for t in topics], both_values, label="Beide Modelle", color="green", height=bar_width)
    plt.barh([topics_dict[t] for t in topics], gpt_only_values, left=both_values, label="Nur GPT-4o", color="skyblue", height=bar_width)
    plt.barh(
        [topics_dict[t] for t in topics],
        deepseek_only_values,
        left=[i + j for i, j in zip(both_values, gpt_only_values)],
        label="Nur Deepseek",
        color="lightcoral",
        height=bar_width
    )

    # Add labels and title in German
    plt.xlabel("Anzahl der zugewiesenen Dateien")
    plt.ylabel("")
    plt.title("Zuweisungen durch beide Modelle (gestapelt)")

    # Add legend to the middle right
    plt.legend(
        title="Modellzuweisung",
        loc='center left',
        bbox_to_anchor=(0.6, 0.65),
        fontsize=12,
        title_fontsize=14
    )

    # Show the plot
    plt.tight_layout()
    plt.savefig(args.plot_file, dpi=300)
    print(f"✅ Stacked bar plot saved to: {args.plot_file}")
    plt.show()

