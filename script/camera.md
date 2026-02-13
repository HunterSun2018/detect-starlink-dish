# 相机参数

## 内参

内参是描述相机内部属性的参数，包括焦距、主点（光学中心）坐标、畸变系数等.

## 外参

外参是描述相机在世界坐标系中的位置和姿态的参数，通常包括旋转矩阵和平移向量.


## 原理


## 基于几何模型的单目视觉定位

原理：通过无人机GPS位置、高度（H）、目标像素坐标及相机参数，利用[透视投影模型](https://zhida.zhihu.com/search?content_id=720039749&content_type=Answer&match_order=1&q=%E9%80%8F%E8%A7%86%E6%8A%95%E5%BD%B1%E6%A8%A1%E5%9E%8B&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3NzExNDc1NzksInEiOiLpgI_op4bmipXlvbHmqKHlnosiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjo3MjAwMzk3NDksImNvbnRlbnRfdHlwZSI6IkFuc3dlciIsIm1hdGNoX29yZGVyIjoxLCJ6ZF90b2tlbiI6bnVsbH0.yklQr07MJoVAXN6N9GuJNvNqlWecKCQDewEFKwbUthE&zhida_source=entity)计算目标三维位置，再转换为地理坐标。

**步骤：**

1.像素→相机坐标系：利用[相机内参矩阵](https://zhida.zhihu.com/search?content_id=720039749&content_type=Answer&match_order=1&q=%E7%9B%B8%E6%9C%BA%E5%86%85%E5%8F%82%E7%9F%A9%E9%98%B5&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3NzExNDc1NzksInEiOiLnm7jmnLrlhoXlj4Lnn6npmLUiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjo3MjAwMzk3NDksImNvbnRlbnRfdHlwZSI6IkFuc3dlciIsIm1hdGNoX29yZGVyIjoxLCJ6ZF90b2tlbiI6bnVsbH0.02vJYn46Ih4rVq2JQiH5Ie2hG3aYswmFfksvGNh8z-8&zhida_source=entity)（焦距、主点）将目标像素坐标转换为归一化平面坐标。

2.相机→机体坐标系：结合无人机姿态角（俯仰、横滚、偏航）进行旋转变换。

3.机体→地理坐标系：结合无人机GPS位置和高度，通过坐标转换链（如NED坐标系）计算目标经纬度。

**适用场景：**已知无人机精确高度（如激光测距）且光照条件良好时，精度可达米级（参考大疆模型）

## **AOA（到达角）定位**

* **方法**：利用单目相机视场角与目标方向角，结合无人机位置解算目标方位。需结合[IMU数据](https://zhida.zhihu.com/search?content_id=720039749&content_type=Answer&match_order=1&q=IMU%E6%95%B0%E6%8D%AE&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3NzExNDc1NzksInEiOiJJTVXmlbDmja4iLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjo3MjAwMzk3NDksImNvbnRlbnRfdHlwZSI6IkFuc3dlciIsIm1hdGNoX29yZGVyIjoxLCJ6ZF90b2tlbiI6bnVsbH0.NsaJoWY5V8SbDCa8GJW37qdPix2vvhZBSIG4NwlQ7OU&zhida_source=entity)补偿姿态扰动

## **融合SLAM的语义定位**

* **算法推荐**：[ORB-SLAM3](https://zhida.zhihu.com/search?content_id=720039749&content_type=Answer&match_order=1&q=ORB-SLAM3&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3NzExNDc1NzksInEiOiJPUkItU0xBTTMiLCJ6aGlkYV9zb3VyY2UiOiJlbnRpdHkiLCJjb250ZW50X2lkIjo3MjAwMzk3NDksImNvbnRlbnRfdHlwZSI6IkFuc3dlciIsIm1hdGNoX29yZGVyIjoxLCJ6ZF90b2tlbiI6bnVsbH0.0381DAb21Z1ulnDxNKDi9qbuYMc_1gjGvzpq4cuBpL8&zhida_source=entity)、[VINS-Fusion](https://zhida.zhihu.com/search?content_id=720039749&content_type=Answer&match_order=1&q=VINS-Fusion&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3NzExNDc1NzksInEiOiJWSU5TLUZ1c2lvbiIsInpoaWRhX3NvdXJjZSI6ImVudGl0eSIsImNvbnRlbnRfaWQiOjcyMDAzOTc0OSwiY29udGVudF90eXBlIjoiQW5zd2VyIiwibWF0Y2hfb3JkZXIiOjEsInpkX3Rva2VuIjpudWxsfQ.Zrk1qnkCPLnSv86WkRaQ6V1IJSlqxk4LmHFbBbPjW7A&zhida_source=entity)、LSD-SLAM（低纹理优化）。
* **优势**：通过SLAM实时构建环境地图并跟踪自身位姿，结合目标检测（YOLO、Faster R-CNN）提供语义约束，提升复杂场景下的鲁棒性。
