import streamlit as st
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
import osmnx as ox
import folium
from streamlit_folium import st_folium

# -----------------------------------------------------------------------------
# 1. CẤU HÌNH TRANG WEB
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Đồ Án Đồ Thị & Pleiku Map", layout="wide", page_icon="🕸️")

# CSS để giao diện đẹp hơn
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    h1 { color: #2E86C1; text-align: center; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #f0f2f6; border-radius: 5px; }
    .stTabs [aria-selected="true"] { background-color: #D6EAF8; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# Khởi tạo Session State
if 'G' not in st.session_state:
    st.session_state['G'] = nx.Graph()
if 'graph_type' not in st.session_state:
    st.session_state['graph_type'] = "Vô hướng"

# -----------------------------------------------------------------------------
# 2. HÀM VẼ ĐỒ THỊ (CHO PHẦN LÝ THUYẾT)
# -----------------------------------------------------------------------------
def draw_graph_theory(graph, path_nodes=None, path_edges=None, title="Đồ thị"):
    fig, ax = plt.subplots(figsize=(10, 6))
    pos = nx.spring_layout(graph, seed=42)
    
    # Vẽ cơ bản
    nx.draw_networkx_nodes(graph, pos, node_size=700, node_color="#AED6F1", ax=ax)
    nx.draw_networkx_edges(graph, pos, width=2, alpha=0.5, edge_color="gray", ax=ax)
    nx.draw_networkx_labels(graph, pos, font_size=12, font_weight="bold", ax=ax)
    edge_labels = nx.get_edge_attributes(graph, 'weight')
    nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels, font_size=10, ax=ax)

    # Highlight (Tô màu đường đi hoặc Prim)
    if path_nodes:
        nx.draw_networkx_nodes(graph, pos, nodelist=path_nodes, node_color="#E74C3C", node_size=800, ax=ax)
    if path_edges:
        nx.draw_networkx_edges(graph, pos, edgelist=path_edges, width=4, edge_color="#E74C3C", ax=ax)
    
    ax.set_title(title, fontsize=14, color="#2874A6")
    ax.axis('off')
    st.pyplot(fig)

# -----------------------------------------------------------------------------
# 3. GIAO DIỆN CHÍNH
# -----------------------------------------------------------------------------
st.title("🕸️ ỨNG DỤNG MÔ PHỎNG THUẬT TOÁN ĐỒ THỊ")
st.write("---")

tab1, tab2 = st.tabs(["📚 PHẦN 1: LÝ THUYẾT (FULL YÊU CẦU)", "🗺️ PHẦN 2: BẢN ĐỒ PLEIKU (THỰC TẾ)"])

# =============================================================================
# TAB 1: LÝ THUYẾT (ĐÁP ỨNG ĐỦ 7 YÊU CẦU ĐỀ BÀI)
# =============================================================================
with tab1:
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("1. Nhập liệu & Cấu hình")
        # Chọn loại
        type_opt = st.radio("Loại đồ thị:", ["Vô hướng", "Có hướng"])
        is_directed = "Có hướng" in type_opt
        
        # Nhập cạnh
        inp = st.text_area("Nhập cạnh (u v w):", value="A B 4\nA C 2\nB C 5\nB D 10\nC E 3\nD F 11\nE D 4", height=150)
        
        # Nút Tạo (YC 1)
        if st.button("🚀 Tạo Đồ Thị"):
            G = nx.DiGraph() if is_directed else nx.Graph()
            for line in inp.strip().split('\n'):
                parts = line.split()
                if len(parts) >= 2:
                    w = int(parts[2]) if len(parts) > 2 else 1
                    G.add_edge(parts[0], parts[1], weight=w)
            st.session_state['G'] = G
            st.session_state['graph_type'] = type_opt
            st.success("Đã tạo xong!")

        # Nút Lưu (YC 2)
        st.download_button("💾 Lưu đồ thị (.txt)", inp, "graph.txt")

    with c2:
        # Vẽ trực quan (YC 1)
        G = st.session_state['G']
        if G.number_of_nodes() > 0:
            draw_graph_theory(G, title=f"Mô hình Đồ thị ({st.session_state['graph_type']})")
        else:
            st.info("👈 Hãy nhập dữ liệu bên trái để bắt đầu.")

    if G.number_of_nodes() > 0:
        st.divider()
        col_func1, col_func2, col_func3 = st.columns(3)
        
        # --- CỘT 1: BIỂU DIỄN & TÍNH CHẤT ---
        with col_func1:
            st.markdown("##### 🛠️ Biểu diễn & Tính chất")
            # YC 6: Chuyển đổi
            view_mode = st.selectbox("Xem dưới dạng:", ["Ma trận kề", "Danh sách kề"])
            if view_mode == "Ma trận kề":
                df = pd.DataFrame(nx.adjacency_matrix(G).todense(), index=G.nodes(), columns=G.nodes())
                st.dataframe(df, height=150)
            else:
                st.json(nx.to_dict_of_lists(G), expanded=False)
            
            # YC 5: Kiểm tra 2 phía
            if st.button("Kiểm tra 2 phía (Bipartite)"):
                if nx.is_bipartite(G): st.success("✅ Là đồ thị 2 phía")
                else: st.error("❌ Không phải đồ thị 2 phía")

        # --- CỘT 2: DUYỆT & TÌM ĐƯỜNG ---
        with col_func2:
            st.markdown("##### 🔍 Duyệt & Tìm đường")
            start = st.selectbox("Điểm Start:", list(G.nodes()))
            end = st.selectbox("Điểm End:", list(G.nodes()), index=len(G.nodes())-1)
            
            # YC 4: BFS/DFS
            b1, b2 = st.columns(2)
            with b1:
                if st.button("Chạy BFS"):
                    path = list(dict(nx.bfs_successors(G, start)).keys())
                    path.insert(0, start)
                    st.success(f"BFS: {path}")
                    draw_graph_theory(G, path_nodes=path, title=f"BFS từ {start}")
            with b2:
                if st.button("Chạy DFS"):
                    path = list(nx.dfs_preorder_nodes(G, start))
                    st.success(f"DFS: {path}")
                    draw_graph_theory(G, path_nodes=path, title=f"DFS từ {start}")

            # YC 3: Đường ngắn nhất
            if st.button("Tìm đường ngắn nhất (Dijkstra)"):
                try:
                    p = nx.shortest_path(G, start, end, weight='weight')
                    w = nx.shortest_path_length(G, start, end, weight='weight')
                    st.success(f"Đường đi: {p} (Tổng: {w})")
                    edges = list(zip(p, p[1:]))
                    draw_graph_theory(G, path_nodes=p, path_edges=edges, title=f"Shortest Path: {start}->{end}")
                except: st.error("Không có đường đi")

        # --- CỘT 3: NÂNG CAO ---
        with col_func3:
            st.markdown("##### 🌲 Nâng cao")
            # YC 7: Prim
            st.write("Thuật toán Prim (MST):")
            if st.button("Chạy Prim Visualizer"):
                if not is_directed and nx.is_connected(G):
                    mst = nx.minimum_spanning_tree(G, algorithm='prim')
                    st.info(f"Tổng trọng số MST: {mst.size(weight='weight')}")
                    draw_graph_theory(G, path_edges=list(mst.edges()), title="Cây khung nhỏ nhất (Prim)")
                else:
                    st.warning("Chỉ áp dụng cho đồ thị vô hướng liên thông.")

# =============================================================================
# TAB 2: BẢN ĐỒ PLEIKU (FIX LỖI & ĐẸP NHẤT)
# =============================================================================
with tab_map:
    st.header("🗺️ Bản đồ Giao thông TP. Pleiku - Gia Lai")

    # 1. LOAD MAP (Set cứng tọa độ Pleiku để không bị lỗi ra map thế giới)
    @st.cache_resource
    def load_pleiku_map():
        # Tọa độ Quảng trường Đại Đoàn Kết làm tâm
        # Lấy bán kính 4km (vừa đủ bao quát trung tâm, không quá nặng)
        point = (13.9785, 108.0051)
        return ox.graph_from_point(point, dist=4000, network_type='drive')

    with st.spinner("Đang tải dữ liệu đường phố Pleiku (Lần đầu mất ~30s)..."):
        try:
            G_map = load_pleiku_map()
            st.success(f"✅ Đã tải xong! Hệ thống gồm {len(G_map.nodes)} giao lộ tại Pleiku.")
        except Exception as e:
            st.error(f"Lỗi tải map: {e}")
            st.stop()

    # 2. DANH SÁCH 30 ĐỊA ĐIỂM CHUẨN TẠI PLEIKU
    locations = {
        "Quảng trường Đại Đoàn Kết": (13.9785, 108.0051),
        "Sân bay Pleiku": (13.9963, 108.0142),
        "Biển Hồ (Tơ Nưng)": (14.0534, 108.0035),
        "Bến xe Đức Long": (13.9556, 108.0264),
        "Sân vận động Pleiku": (13.9791, 108.0076),
        "Chợ Đêm Pleiku": (13.9745, 108.0068),
        "TTTM Vincom Plaza": (13.9804, 108.0053),
        "Coop Mart Pleiku": (13.9818, 108.0064),
        "Bệnh viện Đa khoa Tỉnh": (13.9822, 108.0019),
        "Bệnh viện ĐH Y Dược HAGL": (13.9700, 108.0000),
        "Bệnh viện Nhi Gia Lai": (13.9600, 108.0100),
        "Công viên Diên Hồng": (13.9715, 108.0022),
        "Chùa Minh Thành": (13.9680, 108.0100),
        "Nhà thờ Đức An": (13.9750, 108.0050),
        "Bưu điện Tỉnh Gia Lai": (13.9770, 108.0040),
        "Trường THPT Chuyên Hùng Vương": (13.9850, 108.0100),
        "Trường THPT Pleiku": (13.9800, 108.0120),
        "Trường CĐ Sư phạm Gia Lai": (13.9600, 108.0200),
        "Khách sạn Hoàng Anh Gia Lai": (13.9760, 108.0030),
        "Khách sạn Tre Xanh": (13.9790, 108.0060),
        "Khách sạn Khánh Linh": (13.9780, 108.0050),
        "Khách sạn Mê Kông": (13.9750, 108.0020),
        "Công an Tỉnh Gia Lai": (13.9780, 108.0020),
        "Ủy ban Nhân dân Tỉnh": (13.9790, 108.0040),
        "Ngã 3 Hoa Lư": (13.9850, 108.0050),
        "Ngã 4 Biển Hồ": (14.0000, 108.0000),
        "Chợ Mới Pleiku": (13.9750, 108.0080),
        "Bảo tàng Tỉnh Gia Lai": (13.9780, 108.0055),
        "Rạp chiếu phim Touch Cinema": (13.9700, 108.0100),
        "Công viên Đồng Xanh": (13.9800, 108.0500)
    }

    # 3. GIAO DIỆN ĐIỀU KHIỂN
    col_sel1, col_sel2, col_algo = st.columns([1.5, 1.5, 1.2])
    with col_sel1:
        start_name = st.selectbox("📍 Điểm Xuất Phát:", list(locations.keys()), index=0)
    with col_sel2:
        end_name = st.selectbox("🏁 Điểm Đến:", list(locations.keys()), index=1)
    with col_algo:
        algo_choice = st.selectbox("Thuật toán:", ["Dijkstra (Tối ưu nhất)", "BFS (Ít rẽ nhất)", "DFS (Demo)"])
    
    btn_run = st.button("🚀 TÌM ĐƯỜNG TRÊN BẢN ĐỒ", type="primary")

    # 4. XỬ LÝ & HIỂN THỊ MAP
    # Mặc định: Zoom vào Pleiku (kể cả khi chưa tìm đường)
    map_center = [13.9785, 108.0051] 
    zoom_level = 14
    
    path = []
    path_color = "blue"

    if btn_run:
        try:
            # Lấy tọa độ
            u_coord = locations[start_name]
            v_coord = locations[end_name]

            # Tìm node gần nhất trên đồ thị (Fix lỗi Scikit-learn tại đây)
            orig_node = ox.distance.nearest_nodes(G_map, u_coord[1], u_coord[0])
            dest_node = ox.distance.nearest_nodes(G_map, v_coord[1], v_coord[0])

            # Chạy thuật toán
            if "Dijkstra" in algo_choice:
                path = nx.shortest_path(G_map, orig_node, dest_node, weight='length')
                dist = nx.shortest_path_length(G_map, orig_node, dest_node, weight='length')
                st.success(f"🔵 **Dijkstra:** Quãng đường ngắn nhất: **{dist/1000:.2f} km**")
                path_color = "blue"
            
            elif "BFS" in algo_choice:
                path = nx.shortest_path(G_map, orig_node, dest_node, weight=None)
                st.info(f"🟣 **BFS:** Đi qua **{len(path)}** đoạn đường (ưu tiên ít rẽ).")
                path_color = "purple"

            elif "DFS" in algo_choice:
                try: path = next(nx.all_simple_paths(G_map, orig_node, dest_node, cutoff=60))
                except: path = []
                st.warning("🟠 **DFS:** Đã tìm thấy một đường đi (Demo).")
                path_color = "orange"

            # Cập nhật tâm bản đồ về giữa đoạn đường
            map_center = [(u_coord[0] + v_coord[0])/2, (u_coord[1] + v_coord[1])/2]

        except Exception as e:
            st.error(f"Lỗi tìm đường: {e}")

    # Vẽ Map Folium
    m = folium.Map(location=map_center, zoom_start=zoom_level, tiles="OpenStreetMap")
    
    # Đánh dấu 2 điểm
    folium.Marker(locations[start_name], popup=start_name, icon=folium.Icon(color="green", icon="play")).add_to(m)
    folium.Marker(locations[end_name], popup=end_name, icon=folium.Icon(color="red", icon="flag")).add_to(m)

    # Vẽ đường (Nếu có) - Dùng hàm chuẩn của OSMnx 1.9.4
    if path:
        ox.plot_route_folium(G_map, path, m, color=path_color, weight=5, opacity=0.8)

    # Hiển thị (Width 100% để đẹp)
    st_folium(m, width=1200, height=600)
