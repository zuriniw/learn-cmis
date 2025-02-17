import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


df = pd.read_csv('usertest.csv')
df = df[df['Method'].isin(['init_01', 'init_02', 'init_03'])]


df['Total_Time'] = pd.to_numeric(df['Total_Time'], errors='coerce')
df['Final_Score'] = pd.to_numeric(df['Final_Score'], errors='coerce')
df['Accuracy'] = pd.to_numeric(df['Accuracy'].str.rstrip('%'), errors='coerce') / 100

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

sns.boxplot(x='Method', y='Total_Time', data=df, ax=ax1)
sns.swarmplot(x='Method', y='Total_Time', data=df, color='red', alpha=0.5, ax=ax1)
ax1.set_title('Comparison of Total Time')
ax1.set_ylabel('Total Time (seconds)')

sns.boxplot(x='Method', y='Final_Score', data=df, ax=ax2)
sns.swarmplot(x='Method', y='Final_Score', data=df, color='red', alpha=0.5, ax=ax2)
ax2.set_title('Comparison of Final Scores')
ax2.set_ylabel('Final Score (seconds)')

plt.tight_layout()

print("\n性能统计:")
stats = df.groupby('Method').agg({
    'Total_Time': ['mean', 'std', 'min', 'max'],
    'Final_Score': ['mean', 'std', 'min', 'max']
}).round(2)
print(stats)

plt.savefig('method_comparison.png', dpi=300, bbox_inches='tight')
plt.show()
