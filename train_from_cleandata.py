# @File  : train_from_cleandata.py
# @Author: 沈昌力
# @Date  : 2018/4/9
# @Desc  : pre_process.py处理后的json文件作为-i的输入文件，输出为-c指定的文件，可以设置领域范围-e，邻域线段数-n，是否显示聚类结果-p
from traclus_impl.geometry import Point
import json
from traclus_impl.coordination import train_traclus
import matplotlib.pyplot as plt
from plot_train_res import plot_histogram, plot_one_cluster3, plot_raw2, draw_hist


def first_train(config):
    """
    聚类，并输出聚类结果
    :param config: 配置文件接口
    :return:
    """
    input_file = config.get('first_trian', 'input_file')
    clusters_output_file_name = config.get('first_trian', 'output_file')
    epsilon = config.getfloat('first_trian', 'epsilon')
    min_neighbors = config.getint('first_trian', 'min_neighbors')
    show_clusters_angle_histogram = config.getboolean('first_trian', 'show_clusters_angle_histogram')
    show_clusters = config.getboolean('first_trian', 'show_clusters')
    is_learning_para = config.getboolean('first_trian', 'is_learning_para')

    with open(get_correct_path_to_file(input_file), 'r') as input_stream:
        parsed_input = json.loads(input_stream.read())

    trajs = list(map(lambda traj: list(map(lambda pt: Point(**pt), traj)), parsed_input))
    if show_clusters is True:
        fig_raw = plt.figure('原始航迹')
        plot_raw2(fig_raw, trajs)

    clusters_hook = get_dump_clusters_hook(clusters_output_file_name,
                                           show_clusters_angle_histogram,
                                           show_clusters=show_clusters)
    print("start run_traclus")

    res = train_traclus(point_iterable_list=trajs,
                         epsilon=epsilon,
                         min_neighbors=min_neighbors,
                         min_vertical_lines=2,
                         clusters_hook=clusters_hook,
                         is_learning=is_learning_para)
    if is_learning_para:
        res.sort()
        draw_hist(res)


def get_dump_clusters_hook(
        file_name,
        show_clusters_angle_histogram=False,
        min_num_trajectories_in_cluster=10,
        show_clusters=False):
    if not file_name:
        return None

    def func(clusters, noises):
        mian_cluster_line_segs = []
        small_cluster_line_segs = []
        num_clusters = len(clusters)
        print("一共有%d个簇" % num_clusters)
        index = 1

        for clust in clusters:
            if show_clusters_angle_histogram:
                # 计算角度直方图
                angles = clust.angle_histogram()
                fig = plt.figure(str(index))
                plot_histogram(fig, angles)

            # 统计大簇和小簇
            line_segs = clust.get_trajectory_line_segments()
            dict_output = list(map(lambda traj_line_seg: traj_line_seg.line_segment.as_dict(),
                                   line_segs))

            if show_clusters is True:
                title = '该簇共有' + str(clust.num_trajectories_contained()) + '条线段'
                fig_cluster = plt.figure(title)
                print('开始绘制第%d个簇' % index)
                # 随机取一个颜色作为簇的颜色
                import numpy as np
                color = np.random.randint(16, 255, size=3)
                co = list(map(lambda c: c[2:].upper(), list(map(hex, color))))
                str_corlor = '#' + co[0] + co[1] + co[2]
                # 画簇
                plot_one_cluster3(fig_cluster, dict_output, str_corlor)
                print('绘制第%d个簇完成' % index)

            if clust.num_trajectories_contained() < min_num_trajectories_in_cluster:
                small_cluster_line_segs.append(dict_output)
            else:
                mian_cluster_line_segs.append(dict_output)
            index = index + 1

        noise_cluster_line_segs = list(map(lambda traj_line_seg: traj_line_seg.line_segment.as_dict(), noises))

        print("有%d个主簇" % (len(mian_cluster_line_segs)))
        print("剩下%d个簇认为是小簇" % (len(small_cluster_line_segs)))
        with open(get_correct_path_to_file(file_name), 'w') as output:
            output.write(json.dumps(mian_cluster_line_segs))

        tmp_str = file_name.split('.')
        assert len(tmp_str) == 2
        small_file = tmp_str[0] + '_small.txt'
        with open(get_correct_path_to_file(small_file), 'w') as output:
            output.write(json.dumps(small_cluster_line_segs))

        print("有%d条轨迹线段为噪声" % (len(noise_cluster_line_segs)))
        noise_file = tmp_str[0] + '_noise.txt'
        with open(get_correct_path_to_file(noise_file), 'w') as output:
            output.write(json.dumps(noise_cluster_line_segs))

        if show_clusters_angle_histogram or show_clusters:
            plt.show()
    return func


def get_correct_path_to_file(file_name):
    return file_name

#
# if __name__ == '__main__':
#     main()
