import cv2
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN
#import orb_algo
#from skimage.measure import label, regionprops

def detect_and_cluster_bursts(image_path, eps=30, min_samples=5, display=True):
    # Bild einlesen und in Graustufen konvertieren
    image = cv2.imread(image_path, cv2.IMREAD_COLOR)

    # ORB-Detektor initialisieren und Keypoints finden
    orb = cv2.ORB_create(nfeatures=500, edgeThreshold=0, scaleFactor=1.2)
    keypoints, descriptors = orb.detectAndCompute(image, None)

    # Keypoints in (x, y)-Koordinaten extrahieren
    keypoints_coords = np.array([kp.pt for kp in keypoints])
    image_keypoint= cv2.drawKeypoints(image,keypoints, None)
    # DBSCAN Clustering anwenden
    if len(keypoints_coords) > 0:
        db = DBSCAN(eps=eps, min_samples=min_samples).fit(keypoints_coords)
        labels = db.labels_
    else:  labels = []

    # Bild kopieren, um Cluster zu zeichnen
    #clustered_image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

    
    # Klassifizierte Bursts sammeln
    bursts = []
    burst_positions= []
    
    # Klassifizierte Bursts sammeln
    critical_bursts = []
    non_critical_bursts = []
    rect_positions= []

    # Durch alle Cluster iterieren und jedes Cluster markieren
    unique_labels = set(labels)
    
    for label in unique_labels:
        if label == -1:
            # Rauschen (kein Cluster) ignorieren
            continue
        cluster_points = keypoints_coords[labels == label]
        x_min, y_min = np.min(cluster_points, axis=0)
        x_max, y_max = np.max(cluster_points, axis=0)
        #minr, minc, maxr, maxc = label.bbox
        duration = x_max - x_min  # Breite in Pixeln
        # Klassifiziere basierend auf der Dauer
        if duration >= 5:  # Schwellwert fuer kritische Bursts (entspricht ca. 0.5s)
            critical_bursts.append(label)
            # Punkte im aktuellen Cluster finden
            cluster_points= keypoints_coords[labels == label]
            # Begrenzungsrechteck gruen um Cluster zeichnen
            x_min, y_min = np.min(cluster_points, axis=0)
            x_max, y_max = np.max(cluster_points, axis=0)
            rect_positions.append((x_min,y_min,x_max,y_max))

            cv2.rectangle(image, (int(x_min), int(y_min)), (int(x_max), int(y_max)), (0, 255, 0), 2)
        else:
            non_critical_bursts.append(label)
            cluster_points= keypoints_coords[labels == label]
            # Begrenzungsrechteck rot um Cluster zeichnen
            x_min, y_min = np.min(cluster_points, axis=0)
            x_max, y_max = np.max(cluster_points, axis=0)
            rect_positions.append((x_min,y_min,x_max,y_max))
            cv2.rectangle(image, (int(x_min), int(y_min)), (int(x_max), int(y_max)), (255, 0, 0), 2)

    
    if display:
        fig, ax = plt.subplots()
        plt.imshow(image) 

        ax.set_xticks(np.linspace(0, 495, 6))  # 6 Ticks
        ax.set_xticklabels(np.linspace(0, 25, 6).round(2))  # Zeit in Sekunden

        # y-Achse: 500 Hz bis 1500 Hz
        ax.set_yticks(np.linspace(0, 365, 6))  # 6 Ticks
        ax.set_yticklabels(np.linspace(800, 1200, 6).round(2))  # Frequenz in Hz
        plt.xlabel('Time [s]')
        plt.ylabel('Frequency [Hz]')
        plt.title('Spectrogram 25 Seconds')
        #plt.yscale()
        plt.title("Burst-Erkennung und Clusterbildung mit ORB und DBSCAN")
        plt.savefig('spectrogram2detected.jpg', format='jpg', bbox_inches='tight', pad_inches=0)
        if display:
            plt.show()
            
    return bursts, unique_labels, burst_positions, critical_bursts, non_critical_bursts
'''
def find_matches(image_path1, image_path2):
    image1 = cv2.imread(image_path1, cv2.IMREAD_COLOR)
    image2 = cv2.imread(image_path2, cv2.IMREAD_COLOR)
    orb = cv2.ORB_create(nfeatures=500, edgeThreshold=0, scaleFactor=1.2)
    keypoints1, descriptors1 = orb.detectAndCompute(image1, None)
    keypoints2, descriptors2 = orb.detectAndCompute(image2, None)
    matches = orb_algo.orb_process(image1, image2, display=True)

# Beispiel verwenden
image_path1 = "spectrogram2.jpg"
#image_path2 = "master_burst.jpg"
#image_path1 = "spectrogram2.jpg"
#bursts, labels, burst_positions= detect_and_cluster_bursts(image_path1)
detect_and_cluster_bursts(image_path1)
#find_matches(image_path1, image_path2)
'''
