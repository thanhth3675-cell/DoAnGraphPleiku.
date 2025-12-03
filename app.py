import streamlit as st
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
import osmnx as ox
import folium
from streamlit_folium import st_folium
import warnings

# Tắt cảnh báo
warnings.filterwarnings("ignore")

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="Đồ Án Đồ Thị & Pleiku", layout="wide", page_icon="🗺️")

st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; height: 3em; background-color: #D6EAF8; }
    h1 { color: #2E86C1; text-align: center; }
    .success-box { padding: 10px; background-color: #D4EFDF; border-radius: 5px; color: #1E8449; font-weight: bold; }
    .info-box { padding: 10px; background-color: #D6EAF8; border-radius: 5px; color: #2874A6; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- KHỞI TẠO SESSION STATE (QUAN TRỌNG ĐỂ KHÔNG MẤT KẾT QUẢ) ---
if 'G' not in st.session_state:
    st.session_state['G'] = nx.Graph()
if 'path_nodes' not in st.session_state:
    st.session_state['path_nodes'] = [] # Lưu đường đi
if 'path_msg' not in st.session_state:
    st.session_state['path_msg'] = ""   # Lưu thông báo km
if 'path_color' not in st.session_state:
    st.session_state['path_color'] = "blue"

# 2. HÀM VẼ LÝ THUYẾT (TAB 1)
def draw_graph_theory(graph, path_nodes=None, path_edges=None, title="Đồ thị"):
    fig, ax = plt.subplots(figsize=(10, 6))
    try:
        pos = nx.spring_layout(graph, seed=42)
        nx.draw_networkx_nodes(graph, pos, node_size=700, node_color="#AED6F1", ax=ax)
        nx.draw_networkx_edges(graph, pos, width=2, alpha=0.5, edge_color="gray", ax=ax)
        nx.draw_networkx_labels(graph, pos, font_size=12, font_weight="bold", ax=ax)
        edge_labels = nx.get_edge_attributes(graph, 'weight')
        nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels, font_size=10, ax=ax)

        if path_nodes:
            nx.draw_networkx_nodes(graph, pos, nodelist=path_nodes, node_color="#E74C3C", node_size=800, ax=ax)
        if path_edges:
            nx.draw_networkx_edges(graph, pos, edgelist=path_edges, width=4, edge_color="#E74C3C", ax=ax)
    except: pass
    
    ax.set_title(title, fontsize=14, color="#2874A6")
    ax.axis('off')
    st.pyplot(fig)

# 3. GIAO DIỆN CHÍNH
st.title("🕸️ ỨNG DỤNG TÌM ĐƯỜNG ĐÔ THỊ & BẢN ĐỒ")

tab1, tab2 = st.tabs(["📚 PHẦN 1: LÝ THUYẾT", "🗺️ PHẦN 2: BẢN ĐỒ PLEIKU"])

# --- TAB 1: LÝ THUYẾT ---
with tab1:
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("Nhập liệu")
        type_opt = st.radio("Loại:", ["Vô hướng", "Có hướng"])
        is_directed = "Có hướng" in type_opt
        inp = st.text_area("Cạnh (u v w):", value="A B 4\nA C 2\nB C 5\nB D 10\nC E 3\nD F 11\nE D 4", height=150)
        
        if st.button("🚀 Tạo Đồ Thị (YC1)"):
            G = nx.DiGraph() if is_directed else nx.Graph()
            for line in inp.strip().split('\n'):
                parts = line.split()
                if len(parts) >= 2:
                    w = int(parts[2]) if len(parts) > 2 else 1
                    G.add_edge(parts[0], parts[1], weight=w)
            st.session_state['G'] = G
            st.success("Đã tạo xong!")
        st.download_button("💾 Lưu file", inp, "graph.txt")

    with c2:
        G = st.session_state['G']
        if len(G) > 0: draw_graph_theory(G, title="Mô hình Đồ thị")
        else: st.info("👈 Nhập dữ liệu để hiển thị.")

    if len(G) > 0:
        st.divider()
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write("**Biểu diễn & Tính chất:**")
            mode = st.selectbox("Dạng xem:", ["Ma trận kề", "Danh sách kề"])
            if mode == "Ma trận kề":
                st.dataframe(pd.DataFrame(nx.adjacency_matrix(G).todense(), index=G.nodes(), columns=G.nodes()), height=150)
            else: st.json(nx.to_dict_of_lists(G), expanded=False)
            if st.button("Kiểm tra 2 phía"):
                st.write(f"Kết quả: {'✅ Có' if nx.is_bipartite(G) else '❌ Không'}")

        with col2:
            st.write("**Duyệt & Tìm đường:**")
            s = st.selectbox("Start:", list(G.nodes()))
            e = st.selectbox("End:", list(G.nodes()), index=len(G.nodes())-1)
            b1, b2 = st.columns(2)
            with b1:
                if st.button("BFS"):
                    path = list(dict(nx.bfs_successors(G, s)).keys()); path.insert(0, s)
                    st.success(f"BFS: {path}"); draw_graph_theory(G, path_nodes=path, title="BFS")
            with b2:
                if st.button("DFS"):
                    path = list(nx.dfs_preorder_nodes(G, s))
                    st.success(f"DFS: {path}"); draw_graph_theory(G, path_nodes=path, title="DFS")
            if st.button("Dijkstra"):
                try:
                    p = nx.shortest_path(G, s, e, weight='weight')
                    w = nx.shortest_path_length(G, s, e, weight='weight')
                    st.success(f"Path: {p} (W={w})")
                    edges = list(zip(p, p[1:]))
                    draw_graph_theory(G, path_nodes=p, path_edges=edges, title="Shortest Path")
                except: st.error("Không có đường đi")

        with col3:
            st.write("**Nâng cao:**")
            if st.button("Prim (MST)"):
                if not is_directed and nx.is_connected(G):
                    mst = nx.minimum_spanning_tree(G, algorithm='prim')
                    st.info(f"Tổng W: {mst.size(weight='weight')}")
                    draw_graph_theory(G, path_edges=list(mst.edges()), title="Prim MST")
                else: st.warning("Chỉ chạy trên đồ thị vô hướng liên thông.")

# --- TAB 2: BẢN ĐỒ PLEIKU (ĐÃ FIX LỖI BIẾN MẤT) ---
with tab_map:
    st.header("🗺️ Tìm đường tại TP. Pleiku")

    @st.cache_resource
    def load_pleiku_map():
        # Tăng bán kính lên 10km để bao trùm cả Biển Hồ và Sân bay
        point = (13.9785, 108.0051)
        return ox.graph_from_point(point, dist=10000, network_type='drive')

    with st.spinner("Đang tải bản đồ Pleiku (Lần đầu mất khoảng 60s)..."):
        try:
            G_map = load_pleiku_map()
            st.success(f"✅ Đã tải xong! Sẵn sàng tìm đường.")
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
        "Vincom Plaza": (13.9804, 108.0053),
        "BV Đa khoa Tỉnh": (13.9822, 108.0019),
        "Công viên Diên Hồng": (13.9715, 108.0022),
        "Chùa Minh Thành": (13.9680, 108.0100),
        "Ngã 4 Biển Hồ": (14.0000, 108.0000),
        "KS Hoàng Anh Gia Lai": (13.9760, 108.0030)
    }

    c1, c2, c3 = st.columns([1.5, 1.5, 1.2])
    start_name = c1.selectbox("📍 Điểm đi:", list(locations.keys()), index=0)
    end_name = c2.selectbox("🏁 Điểm đến:", list(locations.keys()), index=2)
    algo_choice = c3.selectbox("Thuật toán:", ["Dijkstra (Ngắn nhất)", "BFS (Ít rẽ nhất)", "DFS (Demo)"])
    
    # Nút tìm đường
    if st.button("🚀 TÌM ĐƯỜNG NGAY", type="primary"):
        try:
            u_coord, v_coord = locations[start_name], locations[end_name]
            
            # Tìm node gần nhất
            orig = ox.distance.nearest_nodes(G_map, u_coord[1], u_coord[0])
            dest = ox.distance.nearest_nodes(G_map, v_coord[1], v_coord[0])

            path = []
            msg = ""
            color = "blue"

            if "Dijkstra" in algo_choice:
                path = nx.shortest_path(G_map, orig, dest, weight='length')
                d = nx.shortest_path_length(G_map, orig, dest, weight='length')
                msg = f"🔵 Dijkstra: Quãng đường ngắn nhất là **{d/1000:.2f} km**"
                color = "blue"
            
            elif "BFS" in algo_choice:
                path = nx.shortest_path(G_map, orig, dest, weight=None)
                msg = f"🟣 BFS: Đi qua **{len(path)}** giao lộ (ưu tiên ít rẽ)."
                color = "purple"
            
            elif "DFS" in algo_choice:
                try: path = next(nx.all_simple_paths(G_map, orig, dest, cutoff=100))
                except: path = []
                msg = "🟠 DFS: Đã tìm thấy một đường đi (mang tính minh họa)." if path else "Không tìm thấy đường DFS."
                color = "orange"

            # LƯU KẾT QUẢ VÀO SESSION STATE (ĐỂ KHÔNG BỊ MẤT KHI RESET)
            st.session_state['path_nodes'] = path
            st.session_state['path_msg'] = msg
            st.session_state['path_color'] = color
            
        except Exception as e:
            st.error(f"Lỗi tính toán: {e}")

    # HIỂN THỊ KẾT QUẢ TỪ SESSION STATE (LUÔN HIỆN)
    if st.session_state['path_msg']:
        if "Dijkstra" in st.session_state['path_msg']:
            st.markdown(f"<div class='success-box'>{st.session_state['path_msg']}</div>", unsafe_allow_html=True)
        else:
            st.info(st.session_state['path_msg'])

    # VẼ BẢN ĐỒ
    # Lấy tâm bản đồ (nếu có đường đi thì lấy tâm đường đi, không thì lấy Pleiku)
    center_map = [13.9785, 108.0051]
    zoom_start = 13
    
    # Tạo bản đồ nền
    m = folium.Map(location=center_map, zoom_start=zoom_start, tiles="OpenStreetMap")
    
    # Marker điểm đầu/cuối
    folium.Marker(locations[start_name], popup=start_name, icon=folium.Icon(color="green", icon="play")).add_to(m)
    folium.Marker(locations[end_name], popup=end_name, icon=folium.Icon(color="red", icon="flag")).add_to(m)

    # VẼ ĐƯỜNG ĐI (LẤY TỪ SESSION STATE)
    if st.session_state['path_nodes']:
        path = st.session_state['path_nodes']
        # Tự vẽ đường (PolyLine) - Cách này bất tử, không bao giờ lỗi
        route_coords = [(G_map.nodes[n]['y'], G_map.nodes[n]['x']) for n in path]
        folium.PolyLine(route_coords, color=st.session_state['path_color'], weight=5, opacity=0.8).add_to(m)
        
        # Fit bản đồ vừa với đường đi
        m.fit_bounds(route_coords)

    # Hiển thị ra màn hình
    st_folium(m, width=1200, height=600)
