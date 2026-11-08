#include <cmath>
#include <cstdint>
#include <memory>
#include <stdexcept>
#include <string>

#include "aruco_msgs/msg/marker_array.hpp"
#include "geometry_msgs/msg/pose_stamped.hpp"
#include "rclcpp/rclcpp.hpp"
#include "tf2/LinearMath/Quaternion.h"
#include "tf2/LinearMath/Vector3.h"

class MarkerToTargetNode : public rclcpp::Node
{
public:
  MarkerToTargetNode()
  : Node("marker_to_target"),
    target_id_(declare_parameter<std::int64_t>("target_id", 201)),
    offset_distance_(declare_parameter<double>("offset_distance", 0.34))
  {
    const auto markers_topic = declare_parameter<std::string>(
      "markers_topic", "/aruco_marker_publisher/markers");
    const auto target_pose_topic = declare_parameter<std::string>(
      "target_pose_topic", "/target_pose");

    if (!std::isfinite(offset_distance_) || offset_distance_ <= 0.0) {
      throw std::invalid_argument("offset_distance must be positive and finite");
    }

    target_publisher_ = create_publisher<geometry_msgs::msg::PoseStamped>(
      target_pose_topic, 10);

    markers_subscription_ = create_subscription<aruco_msgs::msg::MarkerArray>(
      markers_topic, rclcpp::SensorDataQoS(),
      [this](aruco_msgs::msg::MarkerArray::ConstSharedPtr message) {
        publish_target(*message);
      });
  }

private:
  void publish_target(const aruco_msgs::msg::MarkerArray & message)
  {
    for (const auto & marker : message.markers) {
      if (marker.id != target_id_) {
        continue;
      }

      const auto & marker_pose = marker.pose.pose;
      const auto & orientation = marker_pose.orientation;
      tf2::Quaternion marker_rotation(
        orientation.x, orientation.y, orientation.z, orientation.w);

      const double norm_squared = marker_rotation.length2();
      if (!std::isfinite(norm_squared) || norm_squared < 1e-12) {
        return;
      }
      marker_rotation.normalize();

      const auto offset = tf2::quatRotate(
        marker_rotation, tf2::Vector3(0.0, 0.0, offset_distance_));

      // Ruota di 180 gradi attorno alla x locale del marker.
      const tf2::Quaternion flip_x(1.0, 0.0, 0.0, 0.0);
      const auto target_rotation = marker_rotation * flip_x;

      geometry_msgs::msg::PoseStamped target;
      target.header = marker.header.frame_id.empty() ? message.header : marker.header;
      target.pose.position.x = marker_pose.position.x + offset.x();
      target.pose.position.y = marker_pose.position.y + offset.y();
      target.pose.position.z = marker_pose.position.z + offset.z();
      target.pose.orientation.x = target_rotation.x();
      target.pose.orientation.y = target_rotation.y();
      target.pose.orientation.z = target_rotation.z();
      target.pose.orientation.w = target_rotation.w();

      target_publisher_->publish(target);
      return;
    }
  }

  const std::int64_t target_id_;
  const double offset_distance_;
  rclcpp::Publisher<geometry_msgs::msg::PoseStamped>::SharedPtr target_publisher_;
  rclcpp::Subscription<aruco_msgs::msg::MarkerArray>::SharedPtr markers_subscription_;
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<MarkerToTargetNode>());
  rclcpp::shutdown();
  return 0;
}