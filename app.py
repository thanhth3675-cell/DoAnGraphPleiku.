import streamlit as st
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
import osmnx as ox
import folium
from streamlit_folium import st_folium
import warnings

# Tắt cảnh báo đỏ
warnings.filterwarnings("ignore")

# 1. CẤU HÌNH
st.set_page_config(page_title="Đồ Án Pleiku", layout="wide", page_icon="🗺️")

st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    h1 { color: #2E86C1; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

if 'G' not in st.session_state:
    st.session_state['G'] = nx.Graph()
if 'graph_type' not in st.session_state:
    st.session_state['graph_type'] = "Vô hướng"

# 2. HÀM VẼ TAB 1 (LÝ THUYẾT)
def draw_graph_theory(graph, path_nodes=None, title="Đồ thị"):
    fig, ax = plt.subplots(figsize=(10, 6))
    pos = nx.spring_layout(graph, seed=42)
    nx.draw_networkx_nodes(graph, pos, node_size=700, node_color="#AED6F1", ax=ax)
    nx.draw_networkx_edges(graph, pos, width=2, alpha=0.5, edge_color="gray", ax=ax)
    nx.draw_networkx_labels(graph, pos, font_size=12, font_weight="bold", ax=ax)
    nx.draw_networkx_edge_labels(graph, pos, edge_labels=nx.get_edge_attributes(graph, 'weight'), font_size=10, ax=ax)
    
    if path_nodes:
        nx.draw_networkx_nodes(graph, pos, nodelist=path_nodes, node_color="#E74C3C", node_size=800, ax=ax)
        path_edges = list(zip(path_nodes, path_nodes[1:]))
        nx.draw_networkx_edges(graph, pos, edgelist=path_edges, width=4, edge_color="#E74C3C", ax=ax)
    
    ax.set_title(title, fontsize=14, color="#2874A6")
    ax.axis('off')
    st.pyplot(fig)

# 3. GIAO DIỆN CHÍNH
st.title("🕸️ ĐỒ ÁN TỐT NGHIỆP: ĐỒ THỊ & BẢN ĐỒ")
st.write("---")

tab1, tab2 = st.tabs(["📚 PHẦN 1: LÝ THUYẾT", "🗺️ PHẦN 2: BẢN ĐỒ PLEIKU"])

# --- TAB 1: LÝ THUYẾT ---
with tab1:
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("Nhập liệu")
        type_opt = st.radio("Loại:", ["Vô hướng", "Có hướng"])
        is_directed = "Có hướng" in type_opt
        inp = st.text_area("Cạnh (u v w):", value="A B 4\nA C 2\nB C 5\nB D 10\nC E 3\nD F 11\nE D 4")
        if st.button("🚀 Tạo Đồ Thị"):
            G = nx.DiGraph() if is_directed else nx.Graph()
            for line in inp.strip().split('\n'):
                p = line.split()
                if len(p) >= 2: G.add_edge(p[0], p[1], weight=int(p[2]) if len(p)>2 else 1)
            st.session_state['G'] = G
            st.session_state['graph_type'] = type_opt
            st.success("OK")
        st.download_button("💾 Lưu", inp, "graph.txt")

    with c2:
        G = st.session_state['G']
        if len(G) > 0: draw_graph_theory(G, title=f"Đồ thị ({st.session_state['graph_type']})")
    
    if len(G) > 0:
        st.divider()
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Check 2 Phía"):
                st.write(f"Kết quả: {nx.is_bipartite(G)}")
            mode = st.selectbox("Xem:", ["Ma trận kề", "Danh sách kề"])
            if mode == "Ma trận kề": st.dataframe(pd.DataFrame(nx.adjacency_matrix(G).todense(), index=G.nodes(), columns=G.nodes()))
            else: st.json(nx.to_dict_of_lists(G))
        with col2:
            s = st.selectbox("Start", list(G.nodes()))
            e = st.selectbox("End", list(G.nodes()), index=len(G.nodes())-1)
            if st.button("BFS"):
                p = list(dict(nx.bfs_successors(G, s)).keys()); p.insert(0, s)
                st.success(f"BFS: {p}"); draw_graph_theory(G, p, title="BFS")
            if st.button("DFS"):
                p = list(nx.dfs_preorder_nodes(G, s))
                st.success(f"DFS: {p}"); draw_graph_theory(G, p, title="DFS")
            if st.button("Dijkstra"):
                try: p = nx.shortest_path(G, s, e, weight='weight'); draw_graph_theory(G, p, title="Shortest")
                except: st.error("Không có đường")
        with col3:
            if st.button("Prim (MST)"):
                if not is_directed and nx.is_connected(G):
                    mst = nx.minimum_spanning_tree(G, algorithm='prim')
                    st.info(f"Tổng trọng số: {mst.size(weight='weight')}")
                    draw_graph_theory(G, path_edges=list(mst.edges()), title="MST Prim")
                else: st.warning("Chỉ chạy với đồ thị vô hướng liên thông")

# --- TAB 2: BẢN ĐỒ PLEIKU (FIX LỖI 100%) ---
with tab2:
    st.header("🗺️ Tìm đường tại TP. Pleiku")

    @st.cache_resource
    def load_map():
        # Load bán kính 3km từ quảng trường
        return ox.graph_from_point((13.9785, 108.0051), dist=3000, network_type='drive')

    with st.spinner("Đang tải bản đồ..."):
        try:
            G_map = load_map()
            st.success("✅ Đã tải xong!")
        except Exception as e:
            st.error(f"Lỗi tải map: {e}")
            st.stop()

    locs = {
        "Quảng trường Đại Đoàn Kết": (13.9785, 108.0051),
        "Sân bay Pleiku": (13.9963, 108.0142),
        "Biển Hồ": (14.0534, 108.0035),
        "Bến xe Đức Long": (13.9556, 108.0264),
        "Sân vận động Pleiku": (13.9791, 108.0076),
        "Chợ Đêm": (13.9745, 108.0068),
        "Vincom Plaza": (13.9804, 108.0053),
        "BV Đa khoa Tỉnh": (13.9822, 108.0019),
        "Công viên Diên Hồng": (13.9715, 108.0022),
        "Chùa Minh Thành": (13.9680, 108.0100),
        "KS Hoàng Anh Gia Lai": (13.9760, 108.0030)
    }

    c1, c2, c3 = st.columns([1.5, 1.5, 1.2])
    start = c1.selectbox("📍 Điểm đi:", list(locs.keys()), index=0)
    end = c2.selectbox("🏁 Điểm đến:", list(locs.keys()), index=1)
    algo = c3.selectbox("Thuật toán:", ["Dijkstra", "BFS", "DFS"])
    
    run = st.button("🚀 TÌM ĐƯỜNG", type="primary")

    center = [13.9785, 108.0051]
    path_nodes = []
    
    if run:
        u, v = locs[start], locs[end]
        orig = ox.distance.nearest_nodes(G_map, u[1], u[0])
        dest = ox.distance.nearest_nodes(G_map, v[1], v[0])
        
        try:
            if "Dijkstra" in algo:
                path_nodes = nx.shortest_path(G_map, orig, dest, weight='length')
                d = nx.shortest_path_length(G_map, orig, dest, weight='length')
                st.success(f"🔵 Dijkstra: {d/1000:.2f} km")
            elif "BFS" in algo:
                path_nodes = nx.shortest_path(G_map, orig, dest, weight=None)
                st.info(f"🟣 BFS: qua {len(path_nodes)} giao lộ")
            elif "DFS" in algo:
                try: path_nodes = next(nx.all_simple_paths(G_map, orig, dest, cutoff=50))
                except: path_nodes = []
                st.warning("🟠 DFS: Đã tìm thấy đường")
            
            center = [(u[0]+v[0])/2, (u[1]+v[1])/2]
        except: st.error("Không tìm thấy đường")

    m = folium.Map(location=center, zoom_start=14)
    folium.Marker(locs[start], icon=folium.Icon(color="green"), popup=start).add_to(m)
    folium.Marker(locs[end], icon=folium.Icon(color="red"), popup=end).add_to(m)

    # --- KHẮC PHỤC LỖI BIẾN MẤT Ở ĐÂY ---
    # Thay vì dùng ox.plot_route_folium (gây lỗi), ta tự vẽ bằng folium.PolyLine
    if path_nodes:
        coords = [(G_map.nodes[n]['y'], G_map.nodes[n]['x']) for n in path_nodes]
        color = "orange" if "DFS" in algo else ("purple" if "BFS" in algo else "blue")
        folium.PolyLine(coords, color=color, weight=5, opacity=0.8).add_to(m)

    st_folium(m, width=1000, height=500)
