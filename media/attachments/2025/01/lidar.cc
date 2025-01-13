
#include<iostream>
#include<fstream>
#include<ros/ros.h>
#include <cv_bridge/cv_bridge.h>
#include <pcl/point_cloud.h>
#include <pcl/point_types.h>
#include <pcl/io/pcd_io.h>
#include <pcl/visualization/cloud_viewer.h>
#include<pcl/visualization/pcl_visualizer.h>
#include <pcl_conversions/pcl_conversions.h>
#include<pcl/filters/voxel_grid.h>
#include<pcl/filters/passthrough.h>
#include<opencv2/core/core.hpp>
#include <pcl/filters/extract_indices.h>
#include <cmath>
#include <pcl/features/normal_3d_omp.h>
#include <pcl/filters/filter.h>
#include <pcl/registration/icp.h>
#include <pcl/search/kdtree.h>
#include <pcl/common/time.h>
#include <pcl/filters/radius_outlier_removal.h>
#include <pcl/filters/voxel_grid.h>
#include <nav_msgs/GetMap.h>
#include <nav_msgs/OccupancyGrid.h>





using namespace std;
ros::Publisher ocp_map_topic_pub;
ros::Subscriber sub;
nav_msgs::OccupancyGrid occ_map;
// vector<int> slope_id;
pcl::PointCloud<pcl::PointXYZ>::Ptr globalMap(new pcl::PointCloud<pcl::PointXYZ>);
nav_msgs::OccupancyGrid globalgrid;
ros::Publisher pub_pointcloud;
ros::Publisher pub_pointcloud_origin;

void RadiusOutlierFilter(const pcl::PointCloud<pcl::PointXYZ>::Ptr &pcd_cloud0,
                         const double &radius, const int &thre_count) {
  //创建滤波器
  pcl::RadiusOutlierRemoval<pcl::PointXYZ> radiusoutlier;
  //设置输入点云
  radiusoutlier.setInputCloud(pcd_cloud0);
  //设置半径,在该范围内找临近点
  radiusoutlier.setRadiusSearch(radius);
  //设置查询点的邻域点集数，小于该阈值的删除
  radiusoutlier.setMinNeighborsInRadius(thre_count);
  radiusoutlier.filter(*pcd_cloud0);
  // test 保存滤波后的点云到文件
  std::cout << "半径滤波后点云数据点数：" << pcd_cloud0->points.size()
            << std::endl;
}


void cloud_filter(const pcl::PointCloud<pcl::PointXYZ>::Ptr& cloud_source )

{   
    pcl::VoxelGrid<pcl::PointXYZ>  voxel;
  
    // voxel.setLeafSize( 0.02f, 0.02f, 0.02f);
    voxel.setLeafSize( 0.03f, 0.03f, 0.03f);
    voxel.setInputCloud( cloud_source  );
    voxel.filter( *cloud_source );
    // voxel.setInputCloud( cloud_source  );
    // voxel.filter( *cloud_source );


    pcl::NormalEstimationOMP<pcl::PointXYZ,pcl::Normal> n;
    pcl::PointCloud<pcl::Normal>::Ptr normals(new pcl::PointCloud<pcl::Normal>);
    pcl::search::KdTree<pcl::PointXYZ>::Ptr tree(new pcl::search::KdTree<pcl::PointXYZ>());
    n.setNumberOfThreads(15);
    n.setInputCloud(cloud_source);
    n.setSearchMethod(tree);
    n.setRadiusSearch(0.1);
    n.compute(*normals);
    // for (int i=1;i<cloud_source->points.size();)
    // {
    //     if (cloud_source->points[i].y>0.05)
    //     {
    //         cloud_source->erase(cloud_source->begin()+i);
    //         // cloud_source->removeIndices(i);
    //     }
    //     else
    //     {
    //         i=i+1;
    //     }
        
    // }
    for (int i = 1; i < cloud_source->points.size(); i = i + 1)
    {
        float k = abs(normals->points[i].normal_z) / sqrt(normals->points[i].normal_x * normals->points[i].normal_x + normals->points[i].normal_y * normals->points[i].normal_y);
        // if (abs(cloud_source->points[i].x)<0.48 && ((cloud_source->points[i].y)<0.49&&(cloud_source->points[i].y)>-0.45)) {
        //     cloud_source->points[i].x = std::numeric_limits<float>::quiet_NaN();
        //     cloud_source->points[i].y = std::numeric_limits<float>::quiet_NaN();
        //     cloud_source->points[i].z = std::numeric_limits<float>::quiet_NaN();
        // }
       if(k > 1)  //0.2 ~2 之间存在坡度
        {
            if (k < 5)
            {
                cloud_source->points[i].z = cloud_source->points[i].z + 5;
                //slope_id.push_back(i) ;  //坡度点id
            }
            else
            {
//                cloud_source->points[i].x = std::numeric_limits <float>::quiet_NaN();
//                cloud_source->points[i].y = std::numeric_limits <float>::quiet_NaN();
//                cloud_source->points[i].z = std::numeric_limits <float>::quiet_NaN();
                cloud_source->points[i].z =cloud_source->points[i].z +15;
            }
        }


    }
    cloud_source->is_dense =false;
    std::vector<int> maping;
    pcl::removeNaNFromPointCloud(*cloud_source,*cloud_source, maping);
    cloud_source->is_dense =true;

    double thre_radius = 0.1;
    int thres_point_count = 4;
    std::cout << "半径滤波前点云数据点数：" << cloud_source->points.size()<< std::endl;
    RadiusOutlierFilter(cloud_source,thre_radius,thres_point_count);



}


void SetMapTopicMsg(const pcl::PointCloud<pcl::PointXYZ>::Ptr cloud,
                    nav_msgs::OccupancyGrid &msg) {
  msg.header.seq = 0;
  msg.header.stamp = ros::Time::now();
  msg.header.frame_id = "camera_init";

  msg.info.map_load_time = ros::Time::now();
  double map_resolution=0.03;
  msg.info.resolution = map_resolution;

  double x_min, x_max, y_min, y_max;
//   double z_max_grey_rate = 0.05;
//   double z_min_grey_rate = 0.95;
  //? ? ??
//   double k_line =
//       (z_max_grey_rate - z_min_grey_rate) / (thre_z_max - thre_z_min);
//   double b_line =
//       (thre_z_max * z_min_grey_rate - thre_z_min * z_max_grey_rate) /
//       (thre_z_max - thre_z_min);

  if (cloud->points.empty()) {
    ROS_WARN("pcd is empty!\n");
    return;
  }

  for (int i = 0; i < cloud->points.size() - 1; i++) {
    if (i == 0) {
      x_min = x_max = cloud->points[i].x;
      y_min = y_max = cloud->points[i].y;
    }

    double x = cloud->points[i].x;
    double y = cloud->points[i].y;

    if (x < x_min)
      x_min = x;
    if (x > x_max)
      x_max = x;

    if (y < y_min)
      y_min = y;
    if (y > y_max)
      y_max = y;
  }
  // origin的确定
  msg.info.origin.position.x = x_min;
  msg.info.origin.position.y = y_min;
  msg.info.origin.position.z = 0.0;
  msg.info.origin.orientation.x = 0.0;
  msg.info.origin.orientation.y = 0.0;
  msg.info.origin.orientation.z = 0.0;
  msg.info.origin.orientation.w = 1.0;
  //设置栅格地图大小
  msg.info.width = int((x_max - x_min) / map_resolution);
  msg.info.height = int((y_max - y_min) / map_resolution);
  //实际地图中某点坐标为(x,y)，对应栅格地图中坐标为[x*map.info.width+y]
  msg.data.resize(msg.info.width * msg.info.height);
  msg.data.assign(msg.info.width * msg.info.height, 0);

  ROS_INFO("data size = %d\n", msg.data.size());

  for (int iter = 0; iter < cloud->points.size(); iter++) {
    int i = int((cloud->points[iter].x - x_min) / map_resolution);
    if (i < 0 || i >= msg.info.width)
      continue;

    int j = int((cloud->points[iter].y - y_min) / map_resolution);
    if (j < 0 || j >= msg.info.height - 1)
      continue;
    // 栅格地图的占有概率[0,100]，这里设置为占据
    
    msg.data[i + j * msg.info.width] = 100;
    // auto it = std::find(slope_id.begin(),slope_id.end(),i + j * msg.info.width);
    // if(it !=slope_id.end())
    if (cloud->points[iter].z > 10)
        {
            msg.data[i + j * msg.info.width] = 0;
        }
        else if (cloud->points[iter].z > 4)
        {
          msg.data[i + j * msg.info.width] = 50;}
    //    k_line + b_line)) % 255;

  }
}


void pointcloudpublish(const sensor_msgs::PointCloud2ConstPtr& inputMap )
 { 
	//pcl::PointCloud<pcl::PointXYZ> cloud; 
    pcl::PointCloud<pcl::PointXYZ>::Ptr inputMap1(new pcl::PointCloud<pcl::PointXYZ>);

    //     for (int i=1;i<cloud_source->points.size();)
    // {
    //     if (cloud_source->points[i].y>0.05)
    //     {
    //         cloud_source->erase(cloud_source->begin()+i);
    //         // cloud_source->removeIndices(i);
    //     }
    //     else
    //     {
    //         i=i+1;
    //     }cloud_sourc
        
    // }
    sensor_msgs::PointCloud2 output;   //声明的输出的点云的格式

    sensor_msgs::PointCloud2 output_origin;   //声明的输出的点云的格式
    pcl::fromROSMsg(*inputMap,*inputMap1);	
    double thre_radius = 0.1;
    int thres_point_count = 4;
    std::cout << "半径滤波前点云数据点数：" << inputMap1->points.size()<< std::endl;
    RadiusOutlierFilter(inputMap1,thre_radius,thres_point_count);
    *globalMap+=*inputMap1;
    // Eigen::MatrixXf rotate(4,4);
    // rotate << 1,0,0,0,
    //        0,-1,0,0,
    //        0,0,-1,1,
    //        0,0,0,1;
    // pcl::transformPointCloud (*inputMap1, *inputMap1, rotate);
    //  printf("%d",inputMap1->points.size());
    // for (int i=1;i<inputMap1->points.size();)
    // {
    //     printf("%f",inputMap1->points[i].y);
        
    // }
    // std::vector<int> maping;
    // pcl::removeNaNFromPointCloud(*inputMap1,*inputMap1, maping);
    toROSMsg(*globalMap,output_origin);
    cloud_filter(globalMap);
    SetMapTopicMsg(globalMap,occ_map);
    // slope_id.clear();
    ocp_map_topic_pub.publish(occ_map);
    toROSMsg(*globalMap,output);
    output.header.stamp=ros::Time::now();
	  output.header.frame_id  ="camera_init";
	  pub_pointcloud.publish(output);
    output_origin.header.stamp=ros::Time::now();
	  output_origin.header.frame_id  ="camera_init";
	  pub_pointcloud_origin.publish(output_origin);


 }



int main(int argc, char **argv)
{
    ros::init(argc, argv, "RGBD");
    ros::start();
    ros::NodeHandle nh;
    ocp_map_topic_pub =nh.advertise<nav_msgs::OccupancyGrid>("ORB_SALM/occpancy_map", 1);
    pub_pointcloud= nh.advertise<sensor_msgs::PointCloud2> ("/unilidar/PointCloudOutput", 10);
    pub_pointcloud_origin= nh.advertise<sensor_msgs::PointCloud2> ("/unilidar/PointCloudOutput_origin", 10);
    ros::Subscriber sub = nh.subscribe("cloud_registered", 10,pointcloudpublish);
    ros::spin();

    return 0;



}