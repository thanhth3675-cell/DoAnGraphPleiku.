import streamlit as st
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
import osmnx as ox
import folium
from streamlit_folium import st_folium
import warnings

# Tắt cảnh báo đỏ gây khó chịu
warnings.filterwarnings("ignore")

# -----------------------------------------------------------------------------
# 1. CẤU HÌNH TRANG WEB
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Đồ Án Đồ Thị & Pleiku Map", layout="wide", page_icon="🕸️")

st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    h1 { color: #2E86C1; text-align: center; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #f0f2f6; border-radius: 5px; }
    .stTabs [aria-selected="true"] { background-color: #D6EAF8; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

if 'G' not in st.session_state:
    st.session_state['G'] = nx.Graph()
if 'graph_type' not in st.session_state:
    st.session_state['graph_type'] = "Vô hướng"

# -----------------------------------------------------------------------------
# 2. HÀM VẼ ĐỒ THỊ LÝ THUYẾT (TAB 1)
# -----------------------------------------------------------------------------
def draw_graph_theory(graph, path_nodes=None, path_edges=None, title="Đồ thị"):
    fig, ax = plt.subplots(figsize=(10, 6))
    pos = nx.spring_layout(graph, seed=42)
    
    # Vẽ nền
    nx.draw_networkx_nodes(graph, pos, node_size=700, node_color="#AED6F1", ax=ax)
    nx.draw_networkx_edges(graph, pos, width=2, alpha=0.5, edge_color="gray", ax=ax)
    nx.draw_networkx_labels(graph, pos, font_size=12, font_weight="bold", ax=ax)
    edge_labels = nx.get_edge_attributes(graph, 'weight')
    nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels, font_size=10, ax=ax)

    # Vẽ Highlight (Đường đi hoặc Cây khung)
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

tab_theory, tab_map = st.tabs(["📚 PHẦN 1: LÝ THUYẾT (FULL YÊU CẦU)", "🗺️ PHẦN 2: BẢN ĐỒ PLEIKU (THỰC TẾ)"])

# =============================================================================
# TAB 1: LÝ THUYẾT (ĐÁP ỨNG ĐỦ 7 YÊU CẦU)
# =============================================================================
with tab_theory:
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("1. Nhập liệu")
        # YC 6 (Một phần): Đồ thị có hướng/vô hướng
        type_opt = st.radio("Loại:", ["Vô hướng", "Có hướng"])
        is_directed = "Có hướng" in type_opt
        
        # YC 6 (Một phần): Nhập danh sách cạnh
        inp = st.text_area("Cạnh (u v w):", value="A B 4\nA C 2\nB C 5\nB D 10\nC E 3\nD F 11\nE D 4", height=150)
        
        # YC 1: Vẽ đồ thị (Nút khởi tạo)
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
        
        # YC 2: Lưu đồ thị
        st.download_button("💾 Lưu file", inp, "graph.txt")

    with c2:
        G = st.session_state['G']
        if G.number_of_nodes() > 0:
            draw_graph_theory(G, title=f"Mô hình ({st.session_state['graph_type']})")
        else:
            st.info("👈 Nhập dữ liệu để bắt đầu.")

    if G.number_of_nodes() > 0:
        st.divider()
        col1, col2, col3 = st.columns(3)
        
        # --- CỘT 1 ---
        with col1:
            st.markdown("##### 🛠️ Biểu diễn")
            # YC 6: Chuyển đổi Ma trận/Danh sách kề
            mode = st.selectbox("Xem dạng:", ["Ma trận kề", "Danh sách kề"])
            if mode == "Ma trận kề":
                df = pd.DataFrame(nx.adjacency_matrix(G).todense(), index=G.nodes(), columns=G.nodes())
                st.dataframe(df, height=150)
            else: st.json(nx.to_dict_of_lists(G), expanded=False)
            
            # YC 5: Đồ thị 2 phía
            if st.button("Kiểm tra 2 phía"):
                st.write(f"Kết quả: {'✅ Có' if nx.is_bipartite(G) else '❌ Không'}")

        # --- CỘT 2 ---
        with col2:
            st.markdown("##### 🔍 Duyệt & Tìm đường")
            start = st.selectbox("S:", list(G.nodes()))
            end = st.selectbox("E:", list(G.nodes()), index=len(G.nodes())-1)
            
            # YC 4: BFS & DFS
            b1, b2 = st.columns(2)
            with b1:
                if st.button("BFS"):
                    path = list(dict(nx.bfs_successors(G, start)).keys())
                    path.insert(0, start)
                    st.success(f"BFS: {path}")
                    draw_graph_theory(G, path_nodes=path, title="BFS")
            with b2:
                if st.button("DFS"):
                    path = list(nx.dfs_preorder_nodes(G, start))
                    st.success(f"DFS: {path}")
                    draw_graph_theory(G, path_nodes=path, title="DFS")
            
            # YC 3: Đường ngắn nhất
            if st.button("Dijkstra (Shortest)"):
                try:
                    p = nx.shortest_path(G, start, end, weight='weight')
                    draw_graph_theory(G, path_nodes=p, title="Shortest Path")
                except: st.error("Không có đường đi")

        # --- CỘT 3 ---
        with col3:
            st.markdown("##### 🌲 Nâng cao")
            # YC 7: Prim (MST)
            if st.button("Prim (MST)"):
                if not is_directed and nx.is_connected(G):
                    mst = nx.minimum_spanning_tree(G, algorithm='prim')
                    st.info(f"Tổng trọng số: {mst.size(weight='weight')}")
                    draw_graph_theory(G, path_edges=list(mst.edges()), title="MST Prim")
                else: st.warning("Chỉ chạy trên đồ thị vô hướng liên thông.")

# =============================================================================
# TAB 2: BẢN ĐỒ PLEIKU (ĐÃ FIX LỖI VẼ & THÊM DFS)
# =============================================================================
with tab_map:
    st.header("🗺️ Tìm đường tại TP. Pleiku")

    @st.cache_resource
    def load_pleiku_map():
        point = (13.9785, 108.0051)
        return ox.graph_from_point(point, dist=4000, network_type='drive')

    with st.spinner("Đang tải bản đồ..."):
        try:
            G_map = load_pleiku_map()
            st.success("✅ Đã tải xong bản đồ!")
        except Exception as e:
            st.error(f"Lỗi tải map: {e}")
            st.stop()

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

    c1, c2, c3 = st.columns([1.5, 1.5, 1.2])
    start = c1.selectbox("📍 Start:", list(locations.keys()), index=0)
    end = c2.selectbox("🏁 End:", list(locations.keys()), index=1)
    # THÊM LẠI DFS VÀO MENU
    algo = c3.selectbox("Thuật toán:", ["Dijkstra (Tối ưu)", "BFS (Ít rẽ)", "DFS (Demo)"])
    
    run = st.button("🚀 TÌM ĐƯỜNG", type="primary")

    map_center = [13.9785, 108.0051]
    path_nodes = []
    
    if run:
        try:
            u_coord, v_coord = locations[start], locations[end]
            orig = ox.distance.nearest_nodes(G_map, u_coord[1], u_coord[0])
            dest = ox.distance.nearest_nodes(G_map, v_coord[1], v_coord[0])

            if "Dijkstra" in algo:
                path_nodes = nx.shortest_path(G_map, orig, dest, weight='length')
                d = nx.shortest_path_length(G_map, orig, dest, weight='length')
                st.success(f"🔵 Dijkstra: {d/1000:.2f} km")
            elif "BFS" in algo:
                path_nodes = nx.shortest_path(G_map, orig, dest, weight=None)
                st.info(f"🟣 BFS: qua {len(path_nodes)} giao lộ")
            elif "DFS" in algo:
                # Thêm lại logic DFS
                try: path_nodes = next(nx.all_simple_paths(G_map, orig, dest, cutoff=50))
                except: path_nodes = []
                st.warning("🟠 DFS: Đã tìm thấy đường (Minh họa)")

            map_center = [(u_coord[0]+v_coord[0])/2, (u_coord[1]+v_coord[1])/2]
        except Exception as e:
            st.error(f"Lỗi: {e}")

    # KHỞI TẠO MAP
    m = folium.Map(location=map_center, zoom_start=14, tiles="OpenStreetMap")
    folium.Marker(locations[start], icon=folium.Icon(color="green", icon="play"), popup=start).add_to(m)
    folium.Marker(locations[end], icon=folium.Icon(color="red", icon="flag"), popup=end).add_to(m)

    # TỰ VẼ ĐƯỜNG (POLYLINE) - ĐẢM BẢO HIỆN 100%
    if path_nodes:
        route_coords = []
        for node in path_nodes:
            point = G_map.nodes[node]
            route_coords.append((point['y'], point['x']))
        
        # Chọn màu
        color = "orange" if "DFS" in algo else ("purple" if "BFS" in algo else "blue")
        folium.PolyLine(route_coords, color=color, weight=5, opacity=0.8).add_to(m)

    st_folium(m, width=1000, height=500)
