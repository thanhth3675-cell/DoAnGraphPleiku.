import streamlit as st
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import osmnx as ox
import folium
from streamlit_folium import st_folium

# -----------------------------------------------------------------------------
# 1. CẤU HÌNH & KHỞI TẠO (Nền móng cho cả ứng dụng)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Graph Algo & Pleiku Map", layout="wide", page_icon="🕸️")

# CSS tùy chỉnh để giao diện đẹp hơn, đồng bộ màu sắc
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; }
    h1 { color: #2E86C1; }
    .highlight { background-color: #f0f2f6; padding: 10px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# Khởi tạo Session State (Bộ nhớ tạm của ứng dụng)
# Giúp biến G (đồ thị) không bị mất khi bấm nút chạy thuật toán
if 'G' not in st.session_state:
    st.session_state['G'] = nx.Graph()
if 'graph_type' not in st.session_state:
    st.session_state['graph_type'] = "Vô hướng"


# -----------------------------------------------------------------------------
# 2. CÁC HÀM HỖ TRỢ (Dùng chung cho cả bài)
# -----------------------------------------------------------------------------

def draw_graph(graph, path=None, title="Trực quan hóa đồ thị"):
    """
    Hàm vẽ đồ thị chuẩn.
    Nếu có biến 'path' truyền vào, nó sẽ tô màu đỏ con đường đó.
    """
    fig, ax = plt.subplots(figsize=(8, 5))
    pos = nx.spring_layout(graph, seed=42)  # Layout lò xo cố định vị trí

    # Vẽ toàn bộ node và edge mặc định (màu xanh)
    nx.draw_networkx_nodes(graph, pos, node_size=600, node_color="#85C1E9", ax=ax)
    nx.draw_networkx_edges(graph, pos, width=2, alpha=0.5, edge_color="gray", ax=ax)
    nx.draw_networkx_labels(graph, pos, font_size=10, font_weight="bold", ax=ax)

    # Vẽ trọng số
    edge_labels = nx.get_edge_attributes(graph, 'weight')
    nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels, font_size=9, ax=ax)

    # NẾU CÓ ĐƯỜNG ĐI (PATH) -> TÔ MÀU NỔI BẬT
    if path:
        # Tạo danh sách cạnh từ đường đi (path nodes -> edges)
        path_edges = list(zip(path, path[1:]))

        # Vẽ lại các node trên đường đi bằng màu cam
        nx.draw_networkx_nodes(graph, pos, nodelist=path, node_color="#FF5733", node_size=700, ax=ax)
        # Vẽ lại các cạnh trên đường đi bằng màu đỏ đậm
        nx.draw_networkx_edges(graph, pos, edgelist=path_edges, width=4, edge_color="#FF5733", ax=ax)
        ax.set_title(f"{title} (Đường đi: {' -> '.join(path)})", color="#FF5733")
    else:
        ax.set_title(title)

    st.pyplot(fig)


# -----------------------------------------------------------------------------
# 3. GIAO DIỆN CHÍNH (MAIN UI)
# -----------------------------------------------------------------------------
st.title("🕸️ Ứng dụng Demo: Lý thuyết Đồ thị & Bản đồ Pleiku")
st.write("Bài tập lớn: Mô phỏng thuật toán đồ thị và ứng dụng tìm đường thực tế.")

# Chia tab rõ ràng
tab_theory, tab_map = st.tabs(["📚 PHẦN 1: LÝ THUYẾT CƠ BẢN", "🗺️ PHẦN 2: BẢN ĐỒ PLEIKU"])

# =============================================================================
# NỘI DUNG TAB 1: LÝ THUYẾT (Hoàn thiện đầy đủ yêu cầu)
# =============================================================================
with tab_theory:
    col_setup, col_viz = st.columns([1, 2])

    # --- KHU VỰC NHẬP LIỆU (Bên trái) ---
    with col_setup:
        st.info("🛠️ **Cấu hình Đồ thị**")

        # Chọn loại đồ thị
        type_option = st.radio("Loại:", ["Vô hướng (Undirected)", "Có hướng (Directed)"])
        is_directed = True if "Có hướng" in type_option else False

        # Textbox nhập dữ liệu
        st.write("**Nhập danh sách cạnh:** (Đỉnh1 Đỉnh2 Trọng_số)")
        default_text = "A B 4\nA C 2\nB C 5\nB D 10\nC E 3\nD F 11\nE D 4"
        input_data = st.text_area("Dữ liệu nguồn:", value=default_text, height=150)

        # Nút khởi tạo đồ thị
        if st.button("🚀 Tạo Đồ Thị"):
            try:
                # Tạo graph mới dựa trên lựa chọn
                new_G = nx.DiGraph() if is_directed else nx.Graph()

                # Parse dữ liệu từng dòng
                lines = input_data.strip().split('\n')
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 2:
                        u, v = parts[0], parts[1]
                        w = int(parts[2]) if len(parts) > 2 else 1
                        new_G.add_edge(u, v, weight=w)

                # Lưu vào Session State
                st.session_state['G'] = new_G
                st.session_state['graph_type'] = "Có hướng" if is_directed else "Vô hướng"
                st.success("Đã cập nhật đồ thị!")
            except Exception as e:
                st.error(f"Lỗi nhập liệu: {e}")

        # [Yêu cầu 2] Lưu đồ thị
        st.download_button(
            label="💾 Tải dữ liệu đồ thị (.txt)",
            data=input_data,
            file_name="graph_data.txt",
            mime="text/plain"
        )

    # --- KHU VỰC HIỂN THỊ (Bên phải) ---
    with col_viz:
        G = st.session_state['G']  # Lấy đồ thị từ bộ nhớ

        # [Yêu cầu 1] Vẽ đồ thị
        if G.number_of_nodes() > 0:
            draw_graph(G, title=f"Đồ thị hiện tại ({st.session_state['graph_type']})")
        else:
            st.warning("⚠️ Chưa có dữ liệu. Vui lòng nhấn 'Tạo Đồ Thị'.")

    st.divider()

    # --- KHU VỰC CHỨC NĂNG & THUẬT TOÁN (Phía dưới) ---
    if G.number_of_nodes() > 0:
        # Tạo 3 cột chức năng con cho gọn
        f1, f2, f3 = st.columns(3)

        # [Yêu cầu 6] Chuyển đổi biểu diễn
        with f1:
            st.subheader("1. Biểu diễn dữ liệu")
            # Ma trận kề
            st.caption("Ma trận kề (Adjacency Matrix)")
            matrix = nx.adjacency_matrix(G).todense()
            df_matrix = pd.DataFrame(matrix, index=G.nodes(), columns=G.nodes())
            st.dataframe(df_matrix, height=200)

            # Danh sách kề
            st.caption("Danh sách kề (Adjacency List)")
            st.json(nx.to_dict_of_lists(G), expanded=False)

        # [Yêu cầu 3, 4, 5] Thuật toán cơ bản
        with f2:
            st.subheader("2. Duyệt & Tìm đường")
            start_node = st.selectbox("Chọn điểm xuất phát:", list(G.nodes()))
            end_node = st.selectbox("Chọn điểm đích (cho tìm đường):", list(G.nodes()), index=len(G.nodes()) - 1)

            # BFS Button
            if st.button("Chạy BFS (Chiều rộng)"):
                try:
                    edges = list(nx.bfs_edges(G, start_node))
                    nodes = [start_node] + [v for u, v in edges]
                    st.success(f"Thứ tự BFS: {nodes}")
                    # Vẽ lại đồ thị highlight theo thứ tự BFS (Minh họa đường đi từ start đến nút cuối cùng tìm thấy)
                    draw_graph(G, path=nodes, title="Mô phỏng duyệt BFS")
                except:
                    st.error("Lỗi chạy BFS")

            # DFS Button
            if st.button("Chạy DFS (Chiều sâu)"):
                try:
                    nodes = list(nx.dfs_preorder_nodes(G, start_node))
                    st.success(f"Thứ tự DFS: {nodes}")
                    draw_graph(G, path=nodes, title="Mô phỏng duyệt DFS")
                except:
                    st.error("Lỗi chạy DFS")

            # Shortest Path Button
            if st.button(f"Đường ngắn nhất ({start_node} -> {end_node})"):
                try:
                    path = nx.shortest_path(G, source=start_node, target=end_node, weight='weight')
                    length = nx.shortest_path_length(G, source=start_node, target=end_node, weight='weight')
                    st.success(f"Đường đi: {' → '.join(path)} (Tổng trọng số: {length})")
                    draw_graph(G, path=path, title="Đường đi ngắn nhất (Dijkstra)")
                except nx.NetworkXNoPath:
                    st.error("Không có đường đi giữa 2 điểm này!")

        # [Yêu cầu 5, 7] Tính chất & Nâng cao
        with f3:
            st.subheader("3. Phân tích nâng cao")

            # Kiểm tra 2 phía
            st.write("**Kiểm tra tính chất:**")
            if st.button("Kiểm tra Đồ thị 2 phía (Bipartite)"):
                is_bi = nx.is_bipartite(G)
                if is_bi:
                    st.success("✅ ĐÚNG. Đây là đồ thị 2 phía.")
                    color_map = nx.bipartite.color(G)
                    st.json(color_map)  # Hiển thị màu phân chia
                else:
                    st.error("❌ SAI. Không phải đồ thị 2 phía.")

            st.write("---")

            # Thuật toán Prim
            st.write("**Thuật toán Prim (Cây khung nhỏ nhất):**")
            if st.session_state['graph_type'] == "Có hướng":
                st.warning("⚠️ Prim chỉ chạy trên đồ thị Vô Hướng.")
            else:
                if st.button("Tìm MST (Prim)"):
                    if nx.is_connected(G):
                        mst = nx.minimum_spanning_tree(G, algorithm='prim')
                        total_w = mst.size(weight='weight')
                        st.info(f"Tổng trọng số cây khung: {total_w}")

                        # Vẽ cây khung
                        fig_mst, ax_mst = plt.subplots(figsize=(6, 4))
                        pos_mst = nx.spring_layout(G, seed=42)
                        nx.draw(G, pos_mst, with_labels=True, node_color='#ddd', edge_color='#ddd', ax=ax_mst)
                        nx.draw_networkx_edges(mst, pos_mst, width=3, edge_color='green', ax=ax_mst)
                        ax_mst.set_title("Cây khung nhỏ nhất (MST) - Cạnh xanh lá")
                        st.pyplot(fig_mst)
                    else:
                        st.error("Đồ thị không liên thông, không thể tạo cây khung.")
# =============================================================================
# NỘI DUNG TAB 2: BẢN ĐỒ THỰC TẾ PLEIKU - GIA LAI
# =============================================================================
with tab_map:
    st.header("🗺️ Tìm đường thông minh tại TP. Pleiku")


    # 1. HÀM TẢI BẢN ĐỒ (Dùng @st.cache để không phải tải lại mỗi lần f5)
    @st.cache_resource
    def load_pleiku_graph():
        # Tải mạng lưới giao thông "drive" (xe chạy) của Pleiku
        G_map = ox.graph_from_place("Pleiku, Gia Lai, Vietnam", network_type='drive')
        return G_map


    # Hiển thị trạng thái tải (Loading spinner)
    with st.spinner("Đang tải dữ liệu bản đồ Pleiku từ vệ tinh... (Lần đầu mất khoảng 30s)"):
        try:
            G_map = load_pleiku_graph()
            st.success(f"Đã tải xong! Bản đồ bao gồm {len(G_map.nodes)} giao lộ và {len(G_map.edges)} con đường.")
        except Exception as e:
            st.error(f"Không tải được bản đồ. Lỗi: {e}")
            st.stop()

    # 2. ĐỊNH NGHĨA CÁC ĐỊA ĐIỂM NỔI TIẾNG (Để demo cho nhanh)
    # Tọa độ (Lat, Long) lấy từ Google Maps
    locations = {
        "Sân bay Pleiku": (13.9963, 108.0142),
        "Quảng trường Đại Đoàn Kết": (13.9785, 108.0051),
        "Biển Hồ (Tơ Nưng)": (14.0534, 108.0035),
        "Sân vận động Pleiku": (13.9791, 108.0076),
        "Bệnh viện Đa khoa Tỉnh": (13.9822, 108.0019),
        "Chợ Đêm Pleiku": (13.9745, 108.0068),
        "Công viên Diên Hồng": (13.9715, 108.0022)
    }

    # 3. GIAO DIỆN CHỌN ĐIỂM
    col_sel1, col_sel2, col_btn = st.columns([2, 2, 1])

    with col_sel1:
        start_name = st.selectbox("📍 Điểm Xuất Phát:", list(locations.keys()), index=0)
    with col_sel2:
        end_name = st.selectbox("🏁 Điểm Đến:", list(locations.keys()), index=1)

    # Nút tìm đường
    find_path = col_btn.button("🔍 Tìm đường đi", type="primary")

    # 4. XỬ LÝ TÌM ĐƯỜNG & VẼ BẢN ĐỒ
    # Lấy tọa độ từ tên địa điểm
    start_coords = locations[start_name]  # (lat, lon)
    end_coords = locations[end_name]  # (lat, lon)

    # Tìm node gần nhất trên đồ thị (Vì tọa độ có thể hơi lệch so với đường đi)
    orig_node = ox.distance.nearest_nodes(G_map, start_coords[1], start_coords[0])
    dest_node = ox.distance.nearest_nodes(G_map, end_coords[1], end_coords[0])

    # Tạo bản đồ nền (Folium)
    # Tâm bản đồ là trung điểm của 2 vị trí
    center_lat = (start_coords[0] + end_coords[0]) / 2
    center_lon = (start_coords[1] + end_coords[1]) / 2
    m = folium.Map(location=[center_lat, center_lon], zoom_start=13, tiles="OpenStreetMap")

    # Đánh dấu 2 điểm Start/End
    folium.Marker(start_coords, popup=start_name, icon=folium.Icon(color="green", icon="play")).add_to(m)
    folium.Marker(end_coords, popup=end_name, icon=folium.Icon(color="red", icon="flag")).add_to(m)

    if find_path:
        try:
            # Thuật toán Dijkstra tìm đường ngắn nhất (weight='length' là độ dài thật)
            route = nx.shortest_path(G_map, orig_node, dest_node, weight='length')

            # Tính tổng độ dài (mét -> km)
            length_m = nx.shortest_path_length(G_map, orig_node, dest_node, weight='length')
            st.success(
                f"🛣️ Quãng đường ngắn nhất từ **{start_name}** đến **{end_name}** là: **{length_m / 1000:.2f} km**")

            # Vẽ đường đi lên bản đồ (Màu xanh dương đậm)
            # ox.plot_route_folium giúp vẽ line đẹp bám theo đường cong
            ox.plot_route_folium(G_map, route, m, color="blue", weight=5, opacity=0.7)

        except nx.NetworkXNoPath:
            st.error("Không tìm thấy đường đi giữa 2 địa điểm này (có thể do dữ liệu bản đồ bị ngắt quãng).")
        except Exception as e:
            st.error(f"Lỗi thuật toán: {e}")

    # Hiển thị bản đồ ra màn hình Streamlit
    st_folium(m, width=1200, height=500)