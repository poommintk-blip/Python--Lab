import numpy as np
import matplotlib.pyplot as plt
from sklearn import metrics
from sklearn.metrics import confusion_matrix
from sklearn import datasets

#สามารถสลับกลุ่ม y_pred ที่เหมาะสม เพื่อให้ได้รับค่าความถูกต้องมากสุดเท่าที่จะเป็นไปได้
for index in range(0,len(y_pred)):
    if(y_pred[index]==0):
         y_pred[index] = 1
    elif (y_pred[index]==1):
          y_pred[index] = 0

#สามารถแสดงค่า y_true และ y_pred ที่สลับใหม่
print("Target or Actual Values")
print("y_true: ", y_true)
print("New Predicted Values")
print("y_pred: ", y_pred)

#สามารถแสดงแผนภาพกราฟจุดของข้อมูล y_true และ y_pred ใหม่อีกครั้ง
colors = np.array(['yellow', 'red', 'blue']) # 0=yellow, 1=red, 2=blue
plt.scatter(x=wine.data[:,0], y=wine.data[:,1], c=colors[y_true])
plt.title('y_true')
plt.show()

plt.scatter(x=wine.data[:,0], y=wine.data[:,1], c=colors[y_pred])
plt.title('y_pred')
plt.show()

#สามารถแสดง Confusion Matrix ของ y_true และ y_pred ออกทางจอภาพได้
cm1 = confusion_matrix(y_true, y_pred)
print(" ")
print("Confusion Matrix: ")
print(cm1)

#สามารถประเมินแบบจำลองโดยใช้ Accuracy ได้ โดยแสดงออกทางจอภาพ
#สังเกตค่า Accuracy ที่ได้จาก Problem 1 และ Problem 2 ว่าข้อไหนสูงกว่ากัน
#ถ้าค่า Accuracy ใน Problem 1 สูงกว่า ให้สลับกลุ่ม y_pred ใหม่จนกว่า Problem 2 จะสูงกว่า
acc1 = accuracy_score(y_true, y_pred)
print(" ")
print("Accuracy Score: ")
print(acc1)