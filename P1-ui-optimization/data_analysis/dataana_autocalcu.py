import matplotlib.pyplot as plt
import numpy as np

def plot_relevance_comparison(auto_dict, manual_dict, set_number, ax):

    sorted_keys = sorted(auto_dict.keys(), key=lambda k: auto_dict[k], reverse=True)
    
    auto_values = [float(auto_dict[k]) for k in sorted_keys]
    manual_values = [float(manual_dict.get(k, 0)) for k in sorted_keys]
    
    x = np.arange(len(sorted_keys))
    width = 0.35
    
    ax.bar(x - width/2, auto_values, width, label='Auto', color='skyblue')
    ax.bar(x + width/2, manual_values, width, label='Manual', color='lightcoral')
    
    ax.set_ylabel('Relevance Score')
    ax.set_title(f'Set {set_number}')
    ax.set_xticks(x)
    ax.set_xticklabels(sorted_keys, rotation=45, ha='right')
    ax.legend()
    ax.set_ylim(0, 1.1)


# Create figure
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(10, 8))

# Set 1 - Weather focused
auto1 = {
    'weather': 1.0, 'finance': 0.652, 'fitness': 0.389, 
    'stocks': 0.258, 'events': 0.200, 'time': 0.181, 
    'smarthome': 0.076, 'travel': 0.0, 'music': 0.0, 
    'health': 0.0, 'recipe': 0.0
}
manual1 = {
    'weather': 1.0, 'time': 0.6, 'finance': 0.6,
    'fitness': 0.2, 'stocks': 0.2, 'events': 0.2
}

# Set 2 - Gaming focused
auto2 = {
    'gaming': 1.0, 'weather': 0.953, 'productivity': 0.467,
    'transportation': 0.432, 'cinema': 0.345, 'travel': 0.100,
    'learning': 0.091, 'shopping': 0.0, 'conference': 0.0,
    'library': 0.0, 'time': 0.0
}
manual2 = {
    'gaming': 1.0, 'weather': 1.0, 'productivity': 0.5,
    'transportation': 0.2, 'cinema': 0.2
}

# Set 3 - Photography focused
auto3 = {
    'photography': 1.0, 'meditation': 0.799, 'pet-care': 0.789,
    'garden': 0.739, 'cooking': 0.544, 'crafting': 0.152,
    'productivity': 0.094, 'transportation': 0.085, 'journal': 0.0,
    'music': 0.0, 'shopping': 0.0
}
manual3 = {
    'photography': 1.0, 'garden': 0.5, 'meditation': 0.5,
    'pet-care': 0.5, 'cooking': 0.2
}

# Set 4 - Car/Calendar focused
auto4 = {
    'car': 1.0, 'weather': 0.613, 'calendar': 0.565,
    'movie': 0.144, 'meal': 0.0, 'language': 0.0,
    'budget': 0.0, 'bike': 0.0, 'workout': 0.0,
    'news': 0.0, 'travel': 0.0
}
manual4 = {
    'weather': 1.0, 'calendar': 1.0, 'car': 1.0,
    'movie': 0.2
}

# Create plots
plot_relevance_comparison(auto1, manual1, 1, ax1)
plot_relevance_comparison(auto2, manual2, 2, ax2)
plot_relevance_comparison(auto3, manual3, 3, ax3)
plot_relevance_comparison(auto4, manual4, 4, ax4)

plt.tight_layout()
plt.show()

# Statistical analysis
def calculate_differences(auto_dict, manual_dict):
    common_keys = set(auto_dict.keys()) & set(manual_dict.keys())
    differences = [abs(float(auto_dict[k]) - float(manual_dict[k])) for k in common_keys]
    return np.mean(differences), np.std(differences), len(common_keys)

sets = [(auto1, manual1), (auto2, manual2), (auto3, manual3), (auto4, manual4)]
print("\nStatistical Analysis:")
for i, (auto, manual) in enumerate(sets, 1):
    mean_diff, std_diff, n_common = calculate_differences(auto, manual)
    print(f"\nSet {i}:")
    print(f"Common items: {n_common}")
    print(f"Mean absolute difference: {mean_diff:.3f}")
    print(f"Standard deviation of differences: {std_diff:.3f}")
