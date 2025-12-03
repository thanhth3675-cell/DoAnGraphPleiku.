import streamlit as st
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import osmnx as ox
import folium
from streamlit_folium import st_folium

# -----------------------------------------------------------------------------
# 1. CẤU HÌNH & KHỞI TẠO
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Graph Algo & Pleiku Map", layout="wide", page_icon="🕸️")

# CSS làm đẹp giao diện
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; }
    h1 { color: #2E86C1; }
    </style>
    """, unsafe_allow_html=True)

# Khởi tạo Session State (Bộ nhớ đệm)
if 'G' not in st.session_state:
    st.session_state['G'] = nx.Graph()
if 'graph_type' not in st.session_state:
    st.session_state['graph_type'] = "Vô hướng"

# -----------------------------------------------------------------------------
# 2. HÀM HỖ TRỢ VẼ (CHO TAB 1)
# -----------------------------------------------------------------------------
def draw_graph(graph, path=None, title="Trực quan hóa"):
    fig, ax = plt.subplots(figsize=(8, 5))
    pos = nx.spring_layout(graph, seed=42)
    nx.draw_networkx_nodes(graph, pos, node_size=600, node_color="#85C1E9", ax=ax)
    nx.draw_networkx_edges(graph, pos, width=2, alpha=0.5, edge_color="gray", ax=ax)
    nx.draw_networkx_labels(graph, pos, font_size=10, font_weight="bold", ax=ax)
    edge_labels = nx.get_edge_attributes(graph, 'weight')
    nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels, font_size=9, ax=ax)

    if path: # Tô màu đường đi nếu có
        path_edges = list(zip(path, path[1:]))
        nx.draw_networkx_nodes(graph, pos, nodelist=path, node_color="#FF5733", node_size=700, ax=ax)
        nx.draw_networkx_edges(graph, pos, edgelist=path_edges, width=4, edge_color="#FF5733", ax=ax)
        ax.set_title(f"{title} (Đường đi: {' -> '.join(path)})", color="#FF5733")
    else:
        ax.set_title(title)
    st.pyplot(fig)

# -----------------------------------------------------------------------------
# 3. GIAO DIỆN CHÍNH
# -----------------------------------------------------------------------------
st.title("🕸️ Đồ Án: Lý thuyết Đồ thị & Tìm đường tại Pleiku")
st.write("Mô phỏng thuật toán đồ thị cơ bản và ứng dụng thực tế trên bản đồ giao thông.")

# CHIA TAB
tab_theory, tab_map = st.tabs(["📚 PHẦN 1: LÝ THUYẾT", "🗺️ PHẦN 2: BẢN ĐỒ PLEIKU"])

# =============================================================================
# TAB 1: LÝ THUYẾT
# =============================================================================
with tab_theory:
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("1. Nhập liệu")
        type_opt = st.radio("Loại:", ["Vô hướng", "Có hướng"])
        is_directed = True if "Có hướng" in type_opt else False
        
        default_txt = "A B 4\nA C 2\nB C 5\nB D 10\nC E 3\nD F 11\nE D 4"
        inp = st.text_area("Danh sách cạnh (Đỉnh1 Đỉnh2 Trọng_số):", value=default_txt, height=150)

        if st.button("🚀 Tạo Đồ Thị"):
            try:
                new_G = nx.DiGraph() if is_directed else nx.Graph()
                for line in inp.strip().split('\n'):
                    parts = line.split()
                    if len(parts) >= 2:
                        w = int(parts[2]) if len(parts) > 2 else 1
                        new_G.add_edge(parts[0], parts[1], weight=w)
                st.session_state['G'] = new_G
                st.session_state['graph_type'] = type_opt
                st.success("Đã cập nhật!")
            except Exception as e: st.error(f"Lỗi: {e}")

        st.download_button("💾 Tải dữ liệu (.txt)", inp, "graph.txt")

    with c2:
        G = st.session_state['G']
        if G.number_of_nodes() > 0:
            draw_graph(G, title=f"Đồ thị ({st.session_state['graph_type']})")
        else:
            st.info("Vui lòng tạo đồ thị trước.")

    if G.number_of_nodes() > 0:
        st.divider()
        f1, f2, f3 = st.columns(3)
        with f1: # YC6
            st.write("###### Biểu diễn")
            st.caption("Ma trận kề")
            st.dataframe(pd.DataFrame(nx.adjacency_matrix(G).todense(), index=G.nodes(), columns=G.nodes()), height=150)
        with f2: # YC3,4
            st.write("###### Duyệt & Tìm đường")
            start = st.selectbox("Start:", list(G.nodes()))
            end = st.selectbox("End:", list(G.nodes()), index=len(G.nodes())-1)
            
            if st.button("BFS (Chiều rộng)"):
                path = list(nx.bfs_tree(G, start)) # Lấy cây BFS
                st.success(f"Duyệt: {path}")
            if st.button("Dijkstra (Ngắn nhất)"):
                try:
                    p = nx.shortest_path(G, start, end, weight='weight')
                    draw_graph(G, path=p, title="Dijkstra Shortest Path")
                except: st.error("Không có đường đi")
        with f3: # YC5,7
            st.write("###### Nâng cao")
            if st.button("Check Bipartite"):
                st.write(f"Kết quả: {'✅ Có' if nx.is_bipartite(G) else '❌ Không'}")
            if st.button("Prim (MST)"):
                if not is_directed and nx.is_connected(G):
                    mst = nx.minimum_spanning_tree(G, algorithm='prim')
                    st.write(f"Tổng trọng số: {mst.size(weight='weight')}")
                else: st.warning("Chỉ dùng cho đồ thị vô hướng liên thông.")

# =============================================================================
# TAB 2: BẢN ĐỒ PLEIKU (ĐÃ CẬP NHẬT CHỌN THUẬT TOÁN)
# =============================================================================
with tab_map:
    st.header("🗺️ Tìm đường thông minh tại TP. Pleiku")

    # 1. Load bản đồ (Cache để chạy nhanh)
    @st.cache_resource
    def load_pleiku_graph():
        return ox.graph_from_place("Pleiku, Gia Lai, Vietnam", network_type='drive')

    with st.spinner("Đang tải dữ liệu Pleiku (Lần đầu mất ~30s)..."):
        try:
            G_map = load_pleiku_graph()
            st.success(f"Đã tải xong! Bản đồ gồm {len(G_map.nodes)} giao lộ.")
        except: st.error("Lỗi tải bản đồ."); st.stop()

    # 2. Địa điểm Demo
    locations = {
        "Sân bay Pleiku": (13.9963, 108.0142),
        "Quảng trường Đại Đoàn Kết": (13.9785, 108.0051),
        "Biển Hồ (Tơ Nưng)": (14.0534, 108.0035),
        "Sân vận động Pleiku": (13.9791, 108.0076),
        "Bệnh viện Đa khoa Tỉnh": (13.9822, 108.0019),
        "Công viên Diên Hồng": (13.9715, 108.0022),
        "Bến xe Đức Long": (13.9556, 108.0264)
    }

    # 3. Điều khiển
    col_s1, col_s2, col_algo = st.columns([1.5, 1.5, 1.5])
    with col_s1:
        start_name = st.selectbox("📍 Điểm đi:", list(locations.keys()), index=0)
    with col_s2:
        end_name = st.selectbox("🏁 Điểm đến:", list(locations.keys()), index=1)
    with col_algo:
        # Chọn thuật toán
        algo_choice = st.selectbox("Chọn thuật toán:", 
                                   ["Dijkstra (Ngắn nhất theo mét)", 
                                    "BFS (Ít ngã rẽ nhất)"])
    
    btn_run = st.button("🚀 Chạy Tìm Đường", type="primary")

    # 4. Xử lý logic
    start_coords = locations[start_name]
    end_coords = locations[end_name]
    orig_node = ox.distance.nearest_nodes(G_map, start_coords[1], start_coords[0])
    dest_node = ox.distance.nearest_nodes(G_map, end_coords[1], end_coords[0])

    # Tạo map nền
    mid_lat = (start_coords[0] + end_coords[0]) / 2
    mid_lon = (start_coords[1] + end_coords[1]) / 2
    m = folium.Map(location=[mid_lat, mid_lon], zoom_start=13)
    
    folium.Marker(start_coords, popup=start_name, icon=folium.Icon(color="green", icon="play")).add_to(m)
    folium.Marker(end_coords, popup=end_name, icon=folium.Icon(color="red", icon="flag")).add_to(m)

    if btn_run:
        path = []
        try:
            if "Dijkstra" in algo_choice:
                # Dijkstra tìm đường ngắn nhất theo độ dài (length)
                path = nx.shortest_path(G_map, orig_node, dest_node, weight='length')
                dist = nx.shortest_path_length(G_map, orig_node, dest_node, weight='length')
                st.success(f"🛣️ **Dijkstra:** Quãng đường ngắn nhất: **{dist/1000:.2f} km**")
                color_path = "blue"
            
            elif "BFS" in algo_choice:
                # BFS tìm đường qua ít cạnh nhất (weight=None) -> Ít ngã rẽ, nhưng có thể đi đường vòng xa hơn
                path = nx.shortest_path(G_map, orig_node, dest_node, weight=None)
                st.info(f"⚡ **BFS:** Tìm thấy đường đi qua **{len(path)}** giao lộ.")
                color_path = "purple"

            # Vẽ đường
            if path:
                ox.plot_route_folium(G_map, path, m, color=color_path, weight=5, opacity=0.7)
            
        except nx.NetworkXNoPath:
            st.error("Không tìm thấy đường đi!")
        except Exception as e:
            st.error(f"Lỗi thuật toán: {e}")

    # Hiển thị Map
    st_folium(m, width=1200, height=500)
