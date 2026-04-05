import matplotlib.pyplot as plt
from supertrend import df

# 1. 创建画布，分为上下两部分（高度比例 3:1）
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True, gridspec_kw={'height_ratios': [3, 1]})

# --- 上图：价格与布林带 ---
ax1.plot(df['timestamp'], df['close'], label='ETH Close Price', color='black', linewidth=1.2)
ax1.plot(df['timestamp'], df['upper_band'], label='Upper Band', color='red', linestyle='--', alpha=0.6)
ax1.plot(df['timestamp'], df['lower_band'], label='Lower Band', color='green', linestyle='--', alpha=0.6)
ax1.plot(df['timestamp'], df['moving_avg'], label='MA (14)', color='blue', alpha=0.4)

# 填充布林带内部区域，增加视觉对比
ax1.fill_between(df['timestamp'], df['lower_band'], df['upper_band'], color='gray', alpha=0.1)

ax1.set_title('NexusQuant: ETH/USDT Technical Analysis', fontsize=14)
ax1.set_ylabel('Price (USDT)')
ax1.legend(loc='upper left')
ax1.grid(True, linestyle=':', alpha=0.5)

# --- 下图：ATR 波动率 ---
ax2.plot(df['timestamp'], df['atr'], label='ATR (14)', color='purple', linewidth=1.5)
ax2.set_title('Volatility Index (ATR)', fontsize=12)
ax2.set_ylabel('ATR Value')
ax2.set_xlabel('Date')
ax2.legend(loc='upper left')
ax2.grid(True, linestyle=':', alpha=0.5)

# 自动调整布局并保存
plt.tight_layout()
plt.savefig('nexusquant_analysis.png')
print("可视化图表已生成并保存为 nexusquant_analysis.png")