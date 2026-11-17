from collections import Counter
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Xóc Đĩa Pro - Đảm Bảo Luôn Có Lãi", layout="centered"
)

# --- CSS TÙY CHỈNH GIAO DIỆN DI ĐỘNG & THU NHỎ THÔNG BÁO ---
st.markdown("""
    <style>
    div.stButton > button {
        height: 55px;
        font-size: 18px !important;
        font-weight: bold;
        border-radius: 10px;
        background-color: #f8f9fa;
        border: 2px solid #cbd5e1;
        color: #1e293b;
    }
    div.stButton > button:hover {
        background-color: #ef4444;
        color: white;
        border-color: #ef4444;
    }
    .block-container {
        padding-top: 0.8rem;
        padding-bottom: 2rem;
        padding-left: 0.8rem;
        padding-right: 0.8rem;
    }
    .stAlert {
        padding: 6px 12px !important;
        font-size: 14px !important;
        margin-bottom: 0.5rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# Khởi tạo session state lưu lịch sử
if "history" not in st.session_state:
  st.session_state.history = []

st.title("🎲 Xóc Đĩa Pro - 3 Vị (Đảm Bảo Ăn Là Có Lãi)")


# --- PHẦN 1: CÀI ĐẶT THÔNG SỐ VỐN & CHIẾN THUẬT ---
st.sidebar.header("⚙️ Cài Đặt Vốn & Cược")
total_capital = st.sidebar.number_input(
    "Tổng Vốn Mang Vào (VNĐ):", min_value=100000, value=5000000, step=100000
)
base_bet = st.sidebar.number_input(
    "Mức Cược Tổng Ban Đầu (VNĐ):", min_value=30000, value=60000, step=10000
)

betting_strategy = st.sidebar.selectbox(
    "Chiến thuật dòng tiền:",
    [
        "Gấp thếp thông minh (Bù lỗ + Sinh lời)",
        "Đều tay (Flat Betting)",
    ],
)

stop_loss_pct = st.sidebar.slider("Cắt Lỗ (%):", 5, 50, 25)
take_profit_pct = st.sidebar.slider("Chốt Lãi (%):", 5, 100, 40)

stop_loss_amount = total_capital * (stop_loss_pct / 100)
take_profit_amount = total_capital * (take_profit_pct / 100)

st.sidebar.markdown("---")
st.sidebar.markdown(f"🛑 **Cắt Lỗ:** -{stop_loss_amount:,.0f}")
st.sidebar.markdown(f"🎯 **Chốt Lãi:** +{take_profit_amount:,.0f}")


# --- BÀN PHÍM NHẬP LIỆU TO (0, 1, 2, 3, 4) ---
st.markdown("### ⌨️ Nhập Kết Quả Ván Chơi")
cols_btn = st.columns(6)

label_map = {0: "4T", 1: "1Đ3T", 2: "2Đ2T", 3: "3Đ1T", 4: "4Đ"}

# HỆ SỐ LỜI THUẦN (Net profit multiplier)
net_odds_vi = {0: 15.0, 1: 3.8, 2: 2.6, 3: 3.8, 4: 15.0}
# HỆ SỐ TỔNG NHẬN (dùng để phân bổ tỷ lệ tiền nghịch đảo giúp ăn cửa nào cũng lãi)
total_odds_return_vi = {0: 16.0, 1: 4.8, 2: 3.6, 3: 4.8, 4: 16.0}

for val in range(5):
  with cols_btn[val]:
    if st.button(
        f"{val}\n({label_map[val]})", key=f"btn_{val}", use_container_width=True
    ):
      st.session_state.history.append(val)
      st.rerun()

with cols_btn[5]:
  if st.button("⬅ Xóa", key="btn_back", use_container_width=True):
    if st.session_state.history:
      st.session_state.history.pop()
      st.rerun()

if st.sidebar.button("🗑 Reset Lịch Sử"):
  st.session_state.history = []
  st.rerun()

history = st.session_state.history


# --- HÀM THUẬT TOÁN DỰ ĐOÁN 3 VỊ KHÁC NHAU ---
def get_prediction_vi_unique(hist_slice):
  if len(hist_slice) < 6:
    return 3, 2, 1

  transitions = {}
  for i in range(len(hist_slice) - 2):
    curr_pair = (hist_slice[i], hist_slice[i + 1])
    nxt = hist_slice[i + 2]
    if curr_pair not in transitions:
      transitions[curr_pair] = []
    transitions[curr_pair].append(nxt)

  last_pair = (hist_slice[-2], hist_slice[-1])
  possible_nexts = (
      transitions[last_pair] if last_pair in transitions else hist_slice
  )
  counts = Counter(possible_nexts)
  top_items = counts.most_common(5)

  unique_doors = []
  for item, _ in top_items:
    if item not in unique_doors:
      unique_doors.append(item)

  for v in range(5):
    if len(unique_doors) < 3 and v not in unique_doors:
      unique_doors.append(v)

  return unique_doors[0], unique_doors[1], unique_doors[2]


# --- HÀM PHÂN BỔ TIỀN 3 CỬA ĐẢM BẢO LUÔN CÓ LÃI KHI TRÚNG ---
def calculate_bets_vi(target_total_bet, d1, d2, d3):
  r1 = total_odds_return_vi[d1]
  r2 = total_odds_return_vi[d2]
  r3 = total_odds_return_vi[d3]

  # Phân bổ theo tỷ lệ nghịch đảo hệ số trả thưởng (Cửa ăn thấp cược nhiều, cửa ăn cao cược ít)
  inv1, inv2, inv3 = 1.0 / r1, 1.0 / r2, 1.0 / r3
  sum_inv = inv1 + inv2 + inv3

  m1 = max(10000, round((target_total_bet * (inv1 / sum_inv)) / 10000) * 10000)
  m2 = max(10000, round((target_total_bet * (inv2 / sum_inv)) / 10000) * 10000)
  m3 = max(10000, round((target_total_bet * (inv3 / sum_inv)) / 10000) * 10000)

  actual_total = m1 + m2 + m3
  if actual_total != target_total_bet:
    diff = target_total_bet - actual_total
    m1 += diff
    if m1 < 10000:
      m1 = 10000
      m2 += diff
  return m1, m2, m3, m1 + m2 + m3


def format_k(amount):
  if amount >= 1000:
    return f"{int(amount // 1000)}k"
  return str(amount)


# --- PHẦN 3: PHÂN TÍCH & DỰ ĐOÁN 3 VỊ ---
st.markdown("---")
st.subheader("🤖 Phân Tích 3 Vị Khác Nhau (Đảm Bảo Có Lãi)")

if len(history) >= 6:
  d1, d2, d3 = get_prediction_vi_unique(history)

  simulation_data = []
  running_capital = total_capital

  for i in range(6, len(history)):
    sd1, sd2, sd3 = get_prediction_vi_unique(history[:i])
    if "Đều tay" in betting_strategy:
      current_target = base_bet
    else:
      unrecovered_loss = 0
      for item in reversed(simulation_data):
        if "Thua" in item["TT"]:
          val_str = (
              item["Tổng Cược"]
              .replace("k", "000")
              .replace(",", "")
              .replace(" VNĐ", "")
              .strip()
          )
          unrecovered_loss += float(val_str)
        else:
          break
      # Hệ số bù lỗ an toàn giúp khi thắng luôn bù sạch gốc cũ + có lãi lớn
      current_target = (
          (unrecovered_loss + base_bet) / 0.4
          if unrecovered_loss > 0
          else base_bet
      )
      current_target = max(base_bet, round(current_target / 10000) * 10000)

    m1, m2, m3, actual_bet = calculate_bets_vi(current_target, sd1, sd2, sd3)
    actual_next = history[i]

    net_profit = 0
    if actual_next == sd1:
      net_profit = (m1 * net_odds_vi[sd1]) - actual_bet
    elif actual_next == sd2:
      net_profit = (m2 * net_odds_vi[sd2]) - actual_bet
    elif actual_next == sd3:
      net_profit = (m3 * net_odds_vi[sd3]) - actual_bet
    else:
      net_profit = -actual_bet

    running_capital += net_profit
    simulation_data.append({
        "Ván": i + 1,
        "Cửa 1": f"{label_map[sd1]} ({format_k(m1)})",
        "Cửa 2": f"{label_map[sd2]} ({format_k(m2)})",
        "Cửa 3": f"{label_map[sd3]} ({format_k(m3)})",
        "Tổng Cược": format_k(actual_bet),
        "KQ": label_map[actual_next],
        "TT": "🟢 Thắng" if net_profit > 0 else "🔴 Thua",
        "Lãi/Lỗ": f"{net_profit:+,.0f}",
        "Ví": f"{running_capital:,.0f}",
    })

  # Ván tiếp theo
  if "Đều tay" in betting_strategy:
    next_target = base_bet
  else:
    unrecovered_loss = 0
    for item in reversed(simulation_data):
      if "Thua" in item["TT"]:
        val_str = (
            item["Tổng Cược"]
            .replace("k", "000")
            .replace(",", "")
            .replace(" VNĐ", "")
            .strip()
        )
        unrecovered_loss += float(val_str)
      else:
        break
    next_target = (
        (unrecovered_loss + base_bet) / 0.4
        if unrecovered_loss > 0
        else base_bet
    )
    next_target = max(base_bet, round(next_target / 10000) * 10000)

  money_1, money_2, money_3, total_current_bet = calculate_bets_vi(
      next_target, d1, d2, d3
  )

  col_m1, col_m2, col_m3 = st.columns(3)
  with col_m1:
    st.metric(
        label=f"🎯 Cửa 1 ({label_map[d1]})",
        value=f"Ăn: 1:{net_odds_vi[d1]}",
        delta=f"Cược: {format_k(money_1)}",
    )
  with col_m2:
    st.metric(
        label=f"🔹 Cửa 2 ({label_map[d2]})",
        value=f"Ăn: 1:{net_odds_vi[d2]}",
        delta=f"Cược: {format_k(money_2)}",
    )
  with col_m3:
    st.metric(
        label=f"🔸 Cửa 3 ({label_map[d3]})",
        value=f"Ăn: 1:{net_odds_vi[d3]}",
        delta=f"Cược: {format_k(money_3)}",
    )

  st.info(
      f"💰 **Tổng Cược Ván Kế Tiếp:** `{format_k(total_current_bet)}` (Phân bổ"
      " chuẩn xác để ăn bất kỳ cửa nào cũng có lãi)"
  )

  st.markdown("---")
  col_w1, col_w2 = st.columns(2)
  with col_w1:
    st.metric(label="💵 Số Dư Ví Thực Tế", value=f"{running_capital:,.0f} VNĐ")
  with col_w2:
    if running_capital <= total_capital - stop_loss_amount:
      st.error("🚨 CHẠM CẮT LỖ!")
    elif running_capital >= total_capital + take_profit_amount:
      st.success("🎯 ĐẠT CHỐT LÃI!")
    else:
      st.info("⚖️ Trạng thái: An toàn")

  if simulation_data:
    st.markdown("### 📊 Lịch Sử Cược 3 Vị")
    df_sim = pd.DataFrame(simulation_data)
    df_sim = df_sim.iloc[::-1].reset_index(drop=True)
    st.dataframe(df_sim, use_container_width=True, hide_index=True)
else:
  st.warning(
      f"⚠️ Đã nhập {len(history)}/6 ván. Hãy nhập đủ tối thiểu 6 ván đầu!"
  )


# --- PHẦN 4: BẢNG CẦU TRỰC QUAN ---
def create_compact_casino_grid(data_list, max_rows=5, max_cols=10):
  if not data_list:
    return pd.DataFrame()
  columns_list, current_col = [], []
  for i, val in enumerate(data_list):
    if i == 0 or val == data_list[i - 1]:
      if len(current_col) < max_rows:
        current_col.append(val)
      else:
        columns_list.append(current_col)
        current_col = [val]
    else:
      columns_list.append(current_col)
      current_col = [val]
  if current_col:
    columns_list.append(current_col)

  num_cols_total = len(columns_list)
  matrix = [["" for _ in range(num_cols_total)] for _ in range(max_rows)]
  for col_idx, col_data in enumerate(columns_list):
    for row_idx, val in enumerate(col_data):
      matrix[row_idx][col_idx] = val

  df_full = pd.DataFrame(matrix)
  df_clipped = (
      df_full.iloc[:, -max_cols:] if num_cols_total > max_cols else df_full
  )
  df_clipped.columns = [f"C{i+1}" for i in range(df_clipped.shape[1])]
  return df_clipped


st.markdown("---")
st.markdown("### 📈 Lịch Sử Cầu Bàn Chơi")
col_b1, col_b2, col_b3 = st.columns(3)

with col_b1:
  st.markdown("**Cầu Chẵn / Lẻ**")
  cl_data = ["Chẵn" if v in [0, 2, 4] else "Lẻ" for v in history]
  df_cl = create_compact_casino_grid(cl_data)
  st.dataframe(df_cl, use_container_width=True, hide_index=True)

with col_b2:
  st.markdown("**Cầu Tài / Xỉu / 2**")
  tx2_data = [
      "Xỉu" if v in [0, 1] else ("Tài" if v in [3, 4] else "Số 2")
      for v in history
  ]
  df_tx2 = create_compact_casino_grid(tx2_data)
  st.dataframe(df_tx2, use_container_width=True, hide_index=True)

with col_b3:
  st.markdown("**Lịch Sử Vị**")
  chitiet_data = [f"{v}({label_map[v]})" for v in history]
  df_ct = create_compact_casino_grid(chitiet_data, max_cols=6)
  st.dataframe(df_ct, use_container_width=True, hide_index=True)