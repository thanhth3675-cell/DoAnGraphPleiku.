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
# 1. CẤU HÌNH & KHỞI TẠO
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Đồ Án Đồ Thị & Pleiku Map", layout="wide", page_icon="🕸️")

# CSS làm đẹp giao diện
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; height: 3em; }
    h1 { color: #2E86C1; text-align: center; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #f0f2f6; border-radius: 5px; }
    .stTabs [aria-selected="true"] { background-color: #D6EAF8; font-weight: bold; }
    .success-msg { padding: 10px; background-color: #D4EFDF; color: #1E8449; border-radius: 5px; font-weight: bold; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# Khởi tạo bộ nhớ (Session State) để không bị mất dữ liệu khi web load lại
if 'G' not in st.session_state:
    st.session_state['G'] = nx.Graph()
if 'path_nodes' not in st.session_state: # Lưu đường đi bản đồ
    st.session_state['path_nodes'] = []
if 'path_info' not in st.session_state: # Lưu thông báo bản đồ
    st.session_state['path_info'] = ""
if 'map_center' not in st.session_state: # Lưu vị trí camera bản đồ
    st.session_state['map_center'] = [13.9785, 108.0051]

# -----------------------------------------------------------------------------
# 2. HÀM VẼ ĐỒ THỊ LÝ THUYẾT (TAB 1)
# -----------------------------------------------------------------------------
def draw_graph_theory(graph, path_nodes=None, path_edges=None, title="Trực quan hóa"):
    fig, ax = plt.subplots(figsize=(10, 6))
    pos = nx.spring_layout(graph, seed=42)
    
    # Vẽ Node & Edge nền
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

tab_theory, tab_map = st.tabs(["📚 PHẦN 1: LÝ THUYẾT (ĐỦ 7 YÊU CẦU)", "🗺️ PHẦN 2: BẢN ĐỒ PLEIKU (NHỎ GỌN)"])

# =============================================================================
# TAB 1: LÝ THUYẾT (Hoàn thành đầy đủ yêu cầu giáo viên)
# =============================================================================
with tab_theory:
    c1, c2 = st.columns([1, 2])
    
    # --- CỘT TRÁI: NHẬP LIỆU ---
    with c1:
        st.subheader("1. Nhập liệu")
        # YC 6: Đồ thị có hướng/vô hướng
        type_opt = st.radio("Loại đồ thị:", ["Vô hướng", "Có hướng"])
        is_directed = "Có hướng" in type_opt
        
        # YC 6: Nhập danh sách cạnh
        default_val = "A B 4\nA C 2\nB C 5\nB D 10\nC E 3\nD F 11\nE D 4"
        inp = st.text_area("Nhập cạnh (u v w):", value=default_val, height=150)
        
        # YC 1: Vẽ đồ thị (Nút khởi tạo)
        if st.button("🚀 Tạo & Vẽ Đồ Thị"):
            G = nx.DiGraph() if is_directed else nx.Graph()
            try:
                for line in inp.strip().split('\n'):
                    parts = line.split()
                    if len(parts) >= 2:
                        w = int(parts[2]) if len(parts) > 2 else 1
                        G.add_edge(parts[0], parts[1], weight=w)
                st.session_state['G'] = G
                st.success("Đã tạo xong!")
            except: st.error("Lỗi dữ liệu nhập!")

        # YC 2: Lưu đồ thị
        st.download_button("💾 Lưu đồ thị (.txt)", inp, "graph.txt")

    # --- CỘT PHẢI: HIỂN THỊ HÌNH ẢNH ---
    with c2:
        G = st.session_state['G']
        if G.number_of_nodes() > 0:
            draw_graph_theory(G, title="Mô hình Đồ thị hiện tại")
        else:
            st.info("👈 Vui lòng nhập dữ liệu và bấm nút Tạo Đồ Thị.")

    # --- KHU VỰC CHỨC NĂNG BÊN DƯỚI ---
    if G.number_of_nodes() > 0:
        st.divider()
        col1, col2, col3 = st.columns(3)
        
        # Cột 1: Biểu diễn & Tính chất
        with col1:
            st.markdown("##### 🛠️ Biểu diễn & Tính chất")
            # YC 6: Chuyển đổi biểu diễn
            mode = st.selectbox("Xem dạng:", ["Ma trận kề", "Danh sách kề"])
            if mode == "Ma trận kề":
                st.dataframe(pd.DataFrame(nx.adjacency_matrix(G).todense(), index=G.nodes(), columns=G.nodes()), height=150)
            else: st.json(nx.to_dict_of_lists(G), expanded=False)
            
            # YC 5: Kiểm tra 2 phía
            if st.button("Kiểm tra 2 phía (Bipartite)"):
                res = "✅ Có" if nx.is_bipartite(G) else "❌ Không"
                st.write(f"Kết quả: {res}")

        # Cột 2: Duyệt & Tìm đường
        with col2:
            st.markdown("##### 🔍 Duyệt & Tìm đường")
            start = st.selectbox("Start:", list(G.nodes()))
            end = st.selectbox("End:", list(G.nodes()), index=len(G.nodes())-1)
            
            # YC 4: BFS & DFS
            b1, b2 = st.columns(2)
            with b1:
                if st.button("BFS"):
                    path = list(dict(nx.bfs_successors(G, start)).keys()); path.insert(0, start)
                    st.success(f"BFS: {path}"); draw_graph_theory(G, path_nodes=path, title="Duyệt BFS")
            with b2:
                if st.button("DFS"):
                    path = list(nx.dfs_preorder_nodes(G, start)); st.success(f"DFS: {path}")
                    draw_graph_theory(G, path_nodes=path, title="Duyệt DFS")
            
            # YC 3: Đường ngắn nhất
            if st.button("Dijkstra (Shortest)"):
                try:
                    p = nx.shortest_path(G, start, end, weight='weight')
                    w = nx.shortest_path_length(G, start, end, weight='weight')
                    st.success(f"Path: {p} (W={w})")
                    draw_graph_theory(G, path_nodes=p, title="Đường đi ngắn nhất")
                except: st.error("Không có đường đi")

        # Cột 3: Nâng cao
        with col3:
            st.markdown("##### 🌲 Nâng cao")
            # YC 7: Prim (MST)
            if st.button("Prim (MST)"):
                if not is_directed and nx.is_connected(G):
                    mst = nx.minimum_spanning_tree(G, algorithm='prim')
                    st.info(f"Tổng W: {mst.size(weight='weight')}")
                    draw_graph_theory(G, path_edges=list(mst.edges()), title="Cây khung Prim (MST)")
                else: st.warning("Chỉ chạy trên đồ thị vô hướng liên thông.")

# =============================================================================
# TAB 2: BẢN ĐỒ PLEIKU (NHỎ GỌN - DỄ DÙNG)
# =============================================================================
with tab_map:
    st.header("🗺️ Tìm đường tại Trung Tâm Pleiku")

    # 1. LOAD MAP (TỐI ƯU HÓA: Chỉ tải bán kính 2.5km - Rất nhẹ)
    @st.cache_resource
    def load_pleiku_map_small():
        # Quảng trường Đại Đoàn Kết
        point = (13.9785, 108.0051)
        # Dist = 2500 mét (2.5 km) -> Chỉ lấy trung tâm cho nhẹ
        return ox.graph_from_point(point, dist=2500, network_type='drive')

    with st.spinner("Đang tải bản đồ trung tâm Pleiku (Siêu nhanh)..."):
        try:
            G_map = load_pleiku_map_small()
            st.success("✅ Đã tải xong! Sẵn sàng tìm đường.")
        except Exception as e:
            st.error(f"Lỗi tải map: {e}")
            st.stop()

    # 2. DANH SÁCH ĐỊA ĐIỂM (Trong bán kính 2.5km)
    locations = {
        "Quảng trường Đại Đoàn Kết": (13.9785, 108.0051),
        "Sân vận động Pleiku": (13.9791, 108.0076),
        "Chợ Đêm Pleiku": (13.9745, 108.0068),
        "Vincom Plaza": (13.9804, 108.0053),
        "Coop Mart Pleiku": (13.9818, 108.0064),
        "Bệnh viện Đa khoa Tỉnh": (13.9822, 108.0019),
        "Công viên Diên Hồng": (13.9715, 108.0022),
        "Bưu điện Tỉnh": (13.9770, 108.0040),
        "Khách sạn Hoàng Anh Gia Lai": (13.9760, 108.0030),
        "Khách sạn Tre Xanh": (13.9790, 108.0060),
        "Ngã 3 Hoa Lư": (13.9850, 108.0050)
    }

    # 3. ĐIỀU KHIỂN
    c_start, c_end, c_algo = st.columns([2, 2, 1.5])
    start_name = c_start.selectbox("📍 Điểm đi:", list(locations.keys()), index=0)
    end_name = c_end.selectbox("🏁 Điểm đến:", list(locations.keys()), index=6)
    algo_choice = c_algo.selectbox("Thuật toán:", ["Dijkstra (Ngắn nhất)", "BFS (Ít rẽ nhất)", "DFS (Demo)"])
    
    # Nút tìm đường
    if st.button("🚀 TÌM ĐƯỜNG NGAY", type="primary"):
        try:
            u_coord, v_coord = locations[start_name], locations[end_name]
            
            # Tìm node gần nhất
            orig = ox.distance.nearest_nodes(G_map, u_coord[1], u_coord[0])
            dest = ox.distance.nearest_nodes(G_map, v_coord[1], v_coord[0])

            path = []
            msg = ""
            
            # Chạy thuật toán
            if "Dijkstra" in algo_choice:
                path = nx.shortest_path(G_map, orig, dest, weight='length')
                d = nx.shortest_path_length(G_map, orig, dest, weight='length')
                msg = f"🔵 Dijkstra: Quãng đường ngắn nhất là **{d/1000:.2f} km**"
                color = "blue"
            
            elif "BFS" in algo_choice:
                path = nx.shortest_path(G_map, orig, dest, weight=None)
                msg = f"🟣 BFS: Đi qua **{len(path)}** giao lộ."
                color = "purple"
            
            elif "DFS" in algo_choice:
                try: path = next(nx.all_simple_paths(G_map, orig, dest, cutoff=100))
                except: path = []
                msg = "🟠 DFS: Đã tìm thấy đường (Minh họa)." if path else "Không tìm thấy đường DFS."
                color = "orange"

            # LƯU VÀO SESSION STATE (Để không bị mất)
            st.session_state['path_nodes'] = path
            st.session_state['path_info'] = msg
            st.session_state['path_color'] = color
            st.session_state['map_center'] = [(u_coord[0]+v_coord[0])/2, (u_coord[1]+v_coord[1])/2]
            
        except Exception as e:
            st.error(f"Lỗi: {e}")

    # 4. HIỂN THỊ KẾT QUẢ (Luôn hiện nếu có dữ liệu trong Session)
    if st.session_state['path_info']:
        st.markdown(f"<div class='success-msg'>{st.session_state['path_info']}</div>", unsafe_allow_html=True)

    # 5. VẼ BẢN ĐỒ
    m = folium.Map(location=st.session_state['map_center'], zoom_start=14, tiles="OpenStreetMap")
    
    # Marker
    folium.Marker(locations[start_name], popup=start_name, icon=folium.Icon(color="green", icon="play")).add_to(m)
    folium.Marker(locations[end_name], popup=end_name, icon=folium.Icon(color="red", icon="flag")).add_to(m)

    # Vẽ đường (Tự vẽ bằng PolyLine - Không bao giờ lỗi)
    if st.session_state['path_nodes']:
        path = st.session_state['path_nodes']
        route_coords = [(G_map.nodes[n]['y'], G_map.nodes[n]['x']) for n in path]
        folium.PolyLine(route_coords, color=st.session_state['path_color'], weight=5, opacity=0.8).add_to(m)

    st_folium(m, width=1000, height=500)
