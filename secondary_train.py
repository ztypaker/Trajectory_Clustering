# @File  : secondary_train.py
# @Author: 沈昌力
# @Date  : 2018/4/10
# @Desc  : 二次训练
import matplotlib.pyplot as plt
from traclus_impl.geometry import Point, LineSegment
from traclus_impl.generic_dbscan import dbscan
from traclus_impl.traclus_dbscan import TrajectoryLineSegmentFactory, BestAvailableClusterCandidateIndex, TrajectoryClusterFactory
import json
import numpy as np

# @click.command()
# @click.option(
#     '--input-file', '-i',
#     help='train_from_cleandata输出的聚类文件名Clusters.txt',
#     required=True)
# @click.option(
#     '--clusters-output-file-name', '-c',
#     help='输出的二次聚类文件', required=True)
# @click.option(
#     '--epsilon', '-e',
#     help='领域范围', required=False)
# @click.option(
#     '--min-neighbors', '-n',
#     help='邻域线段数', required=False)
# def main(input_file,
#          clusters_output_file_name,
#          epsilon=None,
#          min_neighbors=None
#          ):
#     start = time.time()
#     result = secondary_train(input_file,
#                              clusters_output_file_name, epsilon, min_neighbors)
#     end = time.time()
#     print("训练时间为%f" % (end - start))
#     print("train done")


def secondary_train(config):
    """
    二次聚类
    :param config: 配置文件接口
    :return:
    """
    input_file = config.get('secondary_trian', 'input_file')
    clusters_output_file_name = config.get('secondary_trian', 'output_file')
    epsilon = config.getfloat('secondary_trian', 'epsilon')
    min_neighbors = config.getint('secondary_trian', 'min_neighbors')
    show_clusters = config.getboolean('secondary_trian', 'show_clusters')

    tmp_str = input_file.split('.')
    assert len(tmp_str) == 2
    small_file = tmp_str[0] + '_small.txt'
    noise_file = tmp_str[0] + '_noise.txt'

    with open(get_correct_path_to_file(small_file), 'r') as input_stream:
        small_input = json.loads(input_stream.read())
    with open(get_correct_path_to_file(noise_file), 'r') as input_stream:
        noise_input = json.loads(input_stream.read())

    trajectory_line_segment_factory = TrajectoryLineSegmentFactory()
    trajs = combine_input(small_input, noise_input, trajectory_line_segment_factory)

    clusters, noises = dbscan_caller(trajs, epsilon=epsilon, min_neighbors=min_neighbors)

    save_clusters_res(clusters_output_file_name, clusters, noises, min_num_trajectories_in_cluster=3)
    print('计算完毕')
    if show_clusters:
        print('开始绘制二次聚类结果图...')
        show_res(trajs, clusters, noises)


def dbscan_caller(cluster_candidates, epsilon, min_neighbors):
    """
    dbscan接口调用
    :param cluster_candidates: 切分后所有航迹线段
    :param epsilon: dbscan领域范围
    :param min_neighbors: dbscan领域最小线段数
    :return:
    """
    # cluster_candidates为切分后的所有线段
    line_seg_index = BestAvailableClusterCandidateIndex(cluster_candidates, epsilon)
    return dbscan(cluster_candidates_index=line_seg_index,
                  # TrajectoryLineSegmentCandidateIndex(cluster_candidates), \
                  min_neighbors=min_neighbors,
                  cluster_factory=TrajectoryClusterFactory(),
                  getnoise=True)


def combine_input(smallclusters, noise, trajectory_line_segment_factory):
    """
    把输入的小簇和噪声合成航迹线段
    :param smallclusters: 小簇
    :param noise: 噪声
    :param trajectory_line_segment_factory: 线段构造器
    :return: list<LineSegment>类型的航迹
    """
    trajs_raw = []
    import operator
    from functools import reduce
    # trajs_raw = reduce(operator.add, smallclusters)
    trajs_raw = smallclusters
    trajs_raw.append(noise)

    def funtmp(seg):
        start = Point(
            x=seg['start']['x'],
            y=seg['start']['y'],
            C=seg['start']['c'],
            V=seg['start']['v'],
            TIME=seg['start']['time'])
        end = Point(
            x=seg['end']['x'],
            y=seg['end']['y'],
            C=seg['end']['c'],
            V=seg['end']['v'],
            TIME=seg['end']['time'])
        lineseg = LineSegment(start, end)
        return lineseg
    trajs_seg = list(map(lambda traj: list(map(funtmp, traj)), trajs_raw))

    trajectory_ids = [i for i in range(0, len(trajs_seg))]

    def func(traj, trajectory_id):
        def _create_traj_line_seg(line_seg):
            tj = trajectory_line_segment_factory.new_trajectory_line_seg(line_seg, trajectory_id=trajectory_id)
            return tj
        return list(map(_create_traj_line_seg, traj))

    trajectorys = list(map(func, trajs_seg, trajectory_ids))
    return reduce(operator.add, trajectorys)


def save_clusters_res(file_name, clusters, noises, min_num_trajectories_in_cluster):
    """
    保存聚类结果
    :param file_name: 保存的文件
    :param clusters: 聚类结果
    :param noises: 噪声结果
    :param min_num_trajectories_in_cluster: 一个类中允许最小的线段数
    :return:
    """
    all_cluster_line_segs = []
    small_cluster_line_segs = []
    print("一共有%d个簇" % (len(clusters)))
    for clust in clusters:
        line_segs = clust.get_trajectory_line_segments()
        dict_output = list(map(lambda traj_line_seg: traj_line_seg.line_segment.as_dict(),
                               line_segs))
        if clust.num_trajectories_contained() < min_num_trajectories_in_cluster:
            small_cluster_line_segs.append(dict_output)
        else:
            all_cluster_line_segs.append(dict_output)

    noise_cluster_line_segs = list(map(lambda traj_line_seg: traj_line_seg.line_segment.as_dict(), noises))

    print("有%d个主簇" % (len(all_cluster_line_segs)))
    print("剩下%d个簇认为是小簇" % (len(small_cluster_line_segs)))
    with open(get_correct_path_to_file(file_name), 'w') as output:
        output.write(json.dumps(all_cluster_line_segs))

    tmp_str = file_name.split('.')
    assert len(tmp_str) == 2
    small_file = tmp_str[0] + '_small.' + tmp_str[1]
    with open(get_correct_path_to_file(small_file), 'w') as output:
        output.write(json.dumps(small_cluster_line_segs))

    print("有%d条轨迹线段为噪声" % (len(noise_cluster_line_segs)))
    noise_file = tmp_str[0] + '_noise.' + tmp_str[1]
    with open(get_correct_path_to_file(noise_file), 'w') as output:
        output.write(json.dumps(noise_cluster_line_segs))


def get_correct_path_to_file(file_name):
    return file_name


def draw_raw(trajs, title, pic):
    """
    绘制原始航迹图
    :param trajs:航迹信息
    :param title: 图标题
    :param pic: 绘制图容器
    :return:
    """
    x = []
    y = []
    for traj in trajs:
        for pt in traj:
            start = traj.line_segment.start
            end = traj.line_segment.end
            x.clear()
            y.clear()
            x.append(start['x'])
            y.append(start['y'])
            x.append(end['x'])
            y.append(end['y'])
            pic.plot(y, x)  # 调用plot在当前的figure对象中绘图实际
    pic.set_title(title)
    # pic.axis([121, 123, 30.8, 32])


def draw_trajs(trajs, title, pic, color='red'):
    """
    绘制航迹
    :param trajs: 航迹
    :param title: 标题
    :param pic: 图容器
    :param color: 颜色
    :return:
    """
    x = []
    y = []
    for traj in trajs:
        start = traj.line_segment.start
        end = traj.line_segment.end
        x.clear()
        y.clear()
        x.append(start.x)
        y.append(start.y)
        x.append(end.x)
        y.append(end.y)
        pic.plot(y, x, c=color)  # 调用plot在当前的figure对象中绘图实际
    pic.set_title(title)
    # pic.axis([121, 123, 30.8, 32])


def show_res(raw, clusters, noises):
    """
    展示训练结果
    :param raw:原始航迹
    :param clusters: 聚类簇
    :param noises: 噪声
    :return:
    """
    fig = plt.figure()
    a1 = fig.add_subplot(221)
    a2 = fig.add_subplot(222)
    a3 = fig.add_subplot(223)
    # a4 = fig.add_subplot(224)
    draw_trajs(raw, 'raw', a1)

    for c in clusters:
        color = np.random.randint(16, 250, size=3)
        co = list(map(lambda c: c[2:].upper(), list(map(hex, color))))
        str_corlor = '#' + co[0] + co[1] + co[2]
        draw_trajs(c.members, 'clusters', a2, str_corlor)

    draw_trajs(noises, 'noises', a3)
    plt.show()

# if __name__ == '__main__':
#     main()
