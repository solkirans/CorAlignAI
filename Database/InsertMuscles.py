import csv
import json
import mysql.connector
from mysql.connector import Error
import io

def create_connection():
    """
    Connect to the MySQL database 'muscledB'.
    Adjust the host, user, and password as needed.
    """
    connection = mysql.connector.connect(
        host='localhost',
        user='root',      # Replace with your MySQL username
        password='416525',  # Replace with your MySQL password
        database='muscledB'
    )
    return connection

def create_muscles_table(connection):
    """
    Create the Muscles table if it does not already exist.
    The table will have:
      - muscle_id: auto-increment primary key
      - type: the muscle/fascia type (e.g. MUSCLE or FASCIA)
      - side: which side (e.g., Left, Right, Center)
      - name: name of the muscle/fascia
      - primary_region: an integer foreign key referencing Regions(region_id)
      - other_regions: a TEXT field storing a JSON array of region ids
    """
    create_table_query = """
    CREATE TABLE IF NOT EXISTS Muscles (
        muscle_id INT AUTO_INCREMENT PRIMARY KEY,
        type VARCHAR(50),
        side VARCHAR(50),
        name VARCHAR(255),
        primary_region INT,
        other_regions TEXT,
        FOREIGN KEY (primary_region) REFERENCES Regions(region_id)
    );
    """
    cursor = connection.cursor()
    cursor.execute(create_table_query)
    connection.commit()
    cursor.close()

def get_region_id(region_name, cursor):
    """
    Look up the region_id in the Regions table for a given region name.
    If no exact match is found, try removing a trailing " Region" from the name.
    """
    query = "SELECT region_id FROM Regions WHERE region_name = %s"
    cursor.execute(query, (region_name,))
    result = cursor.fetchone()
    if result:
        return result[0]
    # If not found, try stripping " Region" (if present)
    if region_name.endswith(" Region"):
        modified = region_name.replace(" Region", "").strip()
        cursor.execute(query, (modified,))
        result = cursor.fetchone()
        if result:
            return result[0]
    print(f"Warning: Region '{region_name}' not found in Regions table.")
    return None

def process_csv_data(connection, csv_data):
    """
    Process the CSV data containing muscle and fascia information.
    For each row (ignoring the ItemNumber), the function:
      - Looks up the primary region id.
      - Parses the OtherRegions field (if not empty) into a list of region ids.
      - Inserts a record into the Muscles table.
    """
    cursor = connection.cursor()
    # Use StringIO to treat the multi-line string as a file object.
    csv_file = io.StringIO(csv_data)
    reader = csv.reader(csv_file)
    header = next(reader)  # Skip header row

    insert_query = """
    INSERT INTO Muscles (type, side, name, primary_region, other_regions)
    VALUES (%s, %s, %s, %s, %s)
    """

    for row in reader:
        # CSV columns: ItemNumber, Type, PrimaryRegion, Side, Name, OtherRegions
        type_field = row[1].strip()
        primary_region_str = row[2].strip()
        side_field = row[3].strip()
        name_field = row[4].strip()
        other_regions_field = row[5].strip()

        # Lookup primary region id
        primary_region_id = get_region_id(primary_region_str, cursor)

        # Process the OtherRegions field.
        # Expected format: a string like "[]" or "[Cervical]" or "[Head & TMJ Region : Thoracic Region]"
        other_region_ids = []
        if other_regions_field != "[]" and other_regions_field.startswith("[") and other_regions_field.endswith("]"):
            inner = other_regions_field[1:-1].strip()  # remove the surrounding brackets
            if inner:
                # Split using colon as a delimiter; note that the delimiter may be surrounded by spaces.
                regions_list = [r.strip() for r in inner.split(":")]
                for reg in regions_list:
                    rid = get_region_id(reg, cursor)
                    if rid is not None:
                        other_region_ids.append(rid)
        # Convert the list of region ids to a JSON string (this preserves order)
        other_regions_json = json.dumps(other_region_ids)

        data = (type_field, side_field, name_field, primary_region_id, other_regions_json)
        cursor.execute(insert_query, data)

    connection.commit()
    cursor.close()

def main():
    # CSV data with muscle and fascia entries.
    csv_data = """ItemNumber,Type,PrimaryRegion,Side,Name,OtherRegions
1,MUSCLE,Head & TMJ,Left,Masseter,[]
2,MUSCLE,Head & TMJ,Right,Masseter,[]
3,MUSCLE,Head & TMJ,Left,Temporalis,[]
4,MUSCLE,Head & TMJ,Right,Temporalis,[]
5,MUSCLE,Head & TMJ,Left,Medial Pterygoid,[]
6,MUSCLE,Head & TMJ,Right,Medial Pterygoid,[]
7,MUSCLE,Head & TMJ,Left,Lateral Pterygoid,[]
8,MUSCLE,Head & TMJ,Right,Lateral Pterygoid,[]
9,MUSCLE,Head & TMJ,Left,Digastric,[Cervical]
10,MUSCLE,Head & TMJ,Right,Digastric,[Cervical]
11,MUSCLE,Head & TMJ,Left,Mylohyoid,[Cervical]
12,MUSCLE,Head & TMJ,Right,Mylohyoid,[Cervical]
13,MUSCLE,Head & TMJ,Left,Stylohyoid,[Cervical]
14,MUSCLE,Head & TMJ,Right,Stylohyoid,[Cervical]
15,MUSCLE,Head & TMJ,Left,Sternohyoid,[Cervical]
16,MUSCLE,Head & TMJ,Right,Sternohyoid,[Cervical]
17,MUSCLE,Head & TMJ,Left,Sternothyroid,[Cervical]
18,MUSCLE,Head & TMJ,Right,Sternothyroid,[Cervical]
19,MUSCLE,Head & TMJ,Left,Omohyoid,[Cervical]
20,MUSCLE,Head & TMJ,Right,Omohyoid,[Cervical]
21,MUSCLE,Head & TMJ,Left,Thyrohyoid,[Cervical]
22,MUSCLE,Head & TMJ,Right,Thyrohyoid,[Cervical]
23,FASCIA,Head & TMJ,Left,Temporalis Fascia,[]
24,FASCIA,Head & TMJ,Right,Temporalis Fascia,[]
25,FASCIA,Head & TMJ,Left,Superficial Fascia of Face/Scalp,[]
26,FASCIA,Head & TMJ,Right,Superficial Fascia of Face/Scalp,[]
27,MUSCLE,Cervical,Left,Longus Capitis,[]
28,MUSCLE,Cervical,Right,Longus Capitis,[]
29,MUSCLE,Cervical,Left,Longus Colli,[]
30,MUSCLE,Cervical,Right,Longus Colli,[]
31,MUSCLE,Cervical,Left,Rectus Capitis Anterior,[]
32,MUSCLE,Cervical,Right,Rectus Capitis Anterior,[]
33,MUSCLE,Cervical,Left,Sternocleidomastoid,[Head & TMJ Region : Thoracic Region]
34,MUSCLE,Cervical,Right,Sternocleidomastoid,[Head & TMJ Region : Thoracic Region]
35,MUSCLE,Cervical,Left,Scalenes (Anterior),[Thoracic Region]
36,MUSCLE,Cervical,Right,Scalenes (Anterior),[Thoracic Region]
37,MUSCLE,Cervical,Left,Scalenes (Middle),[Thoracic Region]
38,MUSCLE,Cervical,Right,Scalenes (Middle),[Thoracic Region]
39,MUSCLE,Cervical,Left,Scalenes (Posterior),[Thoracic Region]
40,MUSCLE,Cervical,Right,Scalenes (Posterior),[Thoracic Region]
41,MUSCLE,Cervical,Left,Rectus Capitis Posterior Major,[Head & TMJ Region]
42,MUSCLE,Cervical,Right,Rectus Capitis Posterior Major,[Head & TMJ Region]
43,MUSCLE,Cervical,Left,Rectus Capitis Posterior Minor,[Head & TMJ Region]
44,MUSCLE,Cervical,Right,Rectus Capitis Posterior Minor,[Head & TMJ Region]
45,MUSCLE,Cervical,Left,Obliquus Capitis Superior,[Head & TMJ Region]
46,MUSCLE,Cervical,Right,Obliquus Capitis Superior,[Head & TMJ Region]
47,MUSCLE,Cervical,Left,Obliquus Capitis Inferior,[]
48,MUSCLE,Cervical,Right,Obliquus Capitis Inferior,[]
49,MUSCLE,Cervical,Left,Splenius Capitis,[]
50,MUSCLE,Cervical,Right,Splenius Capitis,[]
51,MUSCLE,Cervical,Left,Splenius Cervicis,[]
52,MUSCLE,Cervical,Right,Splenius Cervicis,[]
53,MUSCLE,Cervical,Left,Levator Scapulae,[Shoulder Girdle & Scapular Region]
54,MUSCLE,Cervical,Right,Levator Scapulae,[Shoulder Girdle & Scapular Region]
55,MUSCLE,Cervical,Left,Upper Trapezius,[Head & TMJ Region : Shoulder Girdle & Scapular Region]
56,MUSCLE,Cervical,Right,Upper Trapezius,[Head & TMJ Region : Shoulder Girdle & Scapular Region]
57,FASCIA,Cervical,Center,Nuchal Ligament,[]
58,FASCIA,Cervical,Left,Prevertebral Fascia,[]
59,FASCIA,Cervical,Right,Prevertebral Fascia,[]
60,FASCIA,Cervical,Left,Suboccipital Fascia,[]
61,FASCIA,Cervical,Right,Suboccipital Fascia,[]
62,MUSCLE,Shoulder Girdle & Scapular Region,Left,Middle Trapezius,[Thoracic Region]
63,MUSCLE,Shoulder Girdle & Scapular Region,Right,Middle Trapezius,[Thoracic Region]
64,MUSCLE,Shoulder Girdle & Scapular Region,Left,Lower Trapezius,[Thoracic Region]
65,MUSCLE,Shoulder Girdle & Scapular Region,Right,Lower Trapezius,[Thoracic Region]
66,MUSCLE,Shoulder Girdle & Scapular Region,Left,Rhomboid Major,[Thoracic Region]
67,MUSCLE,Shoulder Girdle & Scapular Region,Right,Rhomboid Major,[Thoracic Region]
68,MUSCLE,Shoulder Girdle & Scapular Region,Left,Rhomboid Minor,[Cervical Region : Thoracic Region]
69,MUSCLE,Shoulder Girdle & Scapular Region,Right,Rhomboid Minor,[Cervical Region : Thoracic Region]
70,MUSCLE,Shoulder Girdle & Scapular Region,Left,Serratus Anterior,[Thoracic Region]
71,MUSCLE,Shoulder Girdle & Scapular Region,Right,Serratus Anterior,[Thoracic Region]
72,MUSCLE,Shoulder Girdle & Scapular Region,Left,Supraspinatus,[]
73,MUSCLE,Shoulder Girdle & Scapular Region,Right,Supraspinatus,[]
74,MUSCLE,Shoulder Girdle & Scapular Region,Left,Infraspinatus,[]
75,MUSCLE,Shoulder Girdle & Scapular Region,Right,Infraspinatus,[]
76,MUSCLE,Shoulder Girdle & Scapular Region,Left,Teres Minor,[]
77,MUSCLE,Shoulder Girdle & Scapular Region,Right,Teres Minor,[]
78,MUSCLE,Shoulder Girdle & Scapular Region,Left,Subscapularis,[]
79,MUSCLE,Shoulder Girdle & Scapular Region,Right,Subscapularis,[]
80,MUSCLE,Shoulder Girdle & Scapular Region,Left,Pectoralis Minor,[Thoracic Region]
81,MUSCLE,Shoulder Girdle & Scapular Region,Right,Pectoralis Minor,[Thoracic Region]
82,MUSCLE,Shoulder Girdle & Scapular Region,Left,Pectoralis Major,[Thoracic Region : Abdominal & Core Region]
83,MUSCLE,Shoulder Girdle & Scapular Region,Right,Pectoralis Major,[Thoracic Region : Abdominal & Core Region]
84,MUSCLE,Shoulder Girdle & Scapular Region,Left,Latissimus Dorsi,[Thoracic Region : Lumbar & Lower Back Region : Pelvic Girdle & Hip Region]
85,MUSCLE,Shoulder Girdle & Scapular Region,Right,Latissimus Dorsi,[Thoracic Region : Lumbar & Lower Back Region : Pelvic Girdle & Hip Region]
86,FASCIA,Shoulder Girdle & Scapular Region,Left,Brachial Fascia,[]
87,FASCIA,Shoulder Girdle & Scapular Region,Right,Brachial Fascia,[]
88,FASCIA,Shoulder Girdle & Scapular Region,Left,Axillary Fascia,[]
89,FASCIA,Shoulder Girdle & Scapular Region,Right,Axillary Fascia,[]
90,MUSCLE,Thoracic Region,Left,Iliocostalis Thoracis,[Lumbar & Lower Back Region]
91,MUSCLE,Thoracic Region,Right,Iliocostalis Thoracis,[Lumbar & Lower Back Region]
92,MUSCLE,Thoracic Region,Left,Longissimus Thoracis,[Lumbar & Lower Back Region]
93,MUSCLE,Thoracic Region,Right,Longissimus Thoracis,[Lumbar & Lower Back Region]
94,MUSCLE,Thoracic Region,Left,Spinalis Thoracis,[Lumbar & Lower Back Region]
95,MUSCLE,Thoracic Region,Right,Spinalis Thoracis,[Lumbar & Lower Back Region]
96,MUSCLE,Thoracic Region,Left,Multifidus (Thoracic),[Lumbar & Lower Back Region]
97,MUSCLE,Thoracic Region,Right,Multifidus (Thoracic),[Lumbar & Lower Back Region]
98,MUSCLE,Thoracic Region,Left,Serratus Posterior Superior,[Cervical Region]
99,MUSCLE,Thoracic Region,Right,Serratus Posterior Superior,[Cervical Region]
100,MUSCLE,Thoracic Region,Left,Serratus Posterior Inferior,[Lumbar & Lower Back Region]
101,MUSCLE,Thoracic Region,Right,Serratus Posterior Inferior,[Lumbar & Lower Back Region]
102,MUSCLE,Thoracic Region,Left,Intercostal Muscles,[]
103,MUSCLE,Thoracic Region,Right,Intercostal Muscles,[]
104,FASCIA,Thoracic Region,Left,Thoracolumbar Fascia (Upper Portion),[Lumbar & Lower Back Region]
105,FASCIA,Thoracic Region,Right,Thoracolumbar Fascia (Upper Portion),[Lumbar & Lower Back Region]
106,FASCIA,Thoracic Region,Left,Costal Pleura & Intercostal Fascia,[]
107,FASCIA,Thoracic Region,Right,Costal Pleura & Intercostal Fascia,[]
108,MUSCLE,Abdominal & Core Region,Left,Rectus Abdominis,[Thoracic Region : Pelvic Girdle & Hip Region]
109,MUSCLE,Abdominal & Core Region,Right,Rectus Abdominis,[Thoracic Region : Pelvic Girdle & Hip Region]
110,MUSCLE,Abdominal & Core Region,Left,External Oblique,[Thoracic Region : Lumbar & Lower Back Region : Pelvic Girdle & Hip Region]
111,MUSCLE,Abdominal & Core Region,Right,External Oblique,[Thoracic Region : Lumbar & Lower Back Region : Pelvic Girdle & Hip Region]
112,MUSCLE,Abdominal & Core Region,Left,Internal Oblique,[Thoracic Region : Lumbar & Lower Back Region : Pelvic Girdle & Hip Region]
113,MUSCLE,Abdominal & Core Region,Right,Internal Oblique,[Thoracic Region : Lumbar & Lower Back Region : Pelvic Girdle & Hip Region]
114,MUSCLE,Abdominal & Core Region,Left,Transversus Abdominis,[Thoracic Region : Lumbar & Lower Back Region : Pelvic Girdle & Hip Region]
115,MUSCLE,Abdominal & Core Region,Right,Transversus Abdominis,[Thoracic Region : Lumbar & Lower Back Region : Pelvic Girdle & Hip Region]
116,MUSCLE,Abdominal & Core Region,Left,Diaphragm,[Thoracic Region : Lumbar & Lower Back Region]
117,MUSCLE,Abdominal & Core Region,Right,Diaphragm,[Thoracic Region : Lumbar & Lower Back Region]
118,MUSCLE,Abdominal & Core Region,Left,Pelvic Floor (Levator Ani Group),[Pelvic Girdle & Hip Region]
119,MUSCLE,Abdominal & Core Region,Right,Pelvic Floor (Levator Ani Group),[Pelvic Girdle & Hip Region]
120,MUSCLE,Abdominal & Core Region,Left,Coccygeus,[Pelvic Girdle & Hip Region]
121,MUSCLE,Abdominal & Core Region,Right,Coccygeus,[Pelvic Girdle & Hip Region]
122,FASCIA,Abdominal & Core Region,Center,Linea Alba,[]
123,FASCIA,Abdominal & Core Region,Left,Rectus Sheath,[]
124,FASCIA,Abdominal & Core Region,Right,Rectus Sheath,[]
125,FASCIA,Abdominal & Core Region,Left,Transversalis Fascia,[]
126,FASCIA,Abdominal & Core Region,Right,Transversalis Fascia,[]
127,FASCIA,Abdominal & Core Region,Center,Central Tendon of Diaphragm,[]
128,MUSCLE,Lumbar & Lower Back Region,Left,Iliocostalis Lumborum,[Thoracic Region]
129,MUSCLE,Lumbar & Lower Back Region,Right,Iliocostalis Lumborum,[Thoracic Region]
130,MUSCLE,Lumbar & Lower Back Region,Left,Longissimus Lumborum,[Thoracic Region]
131,MUSCLE,Lumbar & Lower Back Region,Right,Longissimus Lumborum,[Thoracic Region]
132,MUSCLE,Lumbar & Lower Back Region,Left,Multifidus (Lumbar),[Thoracic Region]
133,MUSCLE,Lumbar & Lower Back Region,Right,Multifidus (Lumbar),[Thoracic Region]
134,MUSCLE,Lumbar & Lower Back Region,Left,Quadratus Lumborum,[Thoracic Region : Pelvic Girdle & Hip Region : Abdominal & Core Region]
135,MUSCLE,Lumbar & Lower Back Region,Right,Quadratus Lumborum,[Thoracic Region : Pelvic Girdle & Hip Region : Abdominal & Core Region]
136,MUSCLE,Lumbar & Lower Back Region,Left,Psoas Major,[Thoracic Region : Abdominal & Core Region : Pelvic Girdle & Hip Region]
137,MUSCLE,Lumbar & Lower Back Region,Right,Psoas Major,[Thoracic Region : Abdominal & Core Region : Pelvic Girdle & Hip Region]
138,MUSCLE,Lumbar & Lower Back Region,Left,Psoas Minor,[Thoracic Region : Abdominal & Core Region : Pelvic Girdle & Hip Region]
139,MUSCLE,Lumbar & Lower Back Region,Right,Psoas Minor,[Thoracic Region : Abdominal & Core Region : Pelvic Girdle & Hip Region]
140,FASCIA,Lumbar & Lower Back Region,Left,Thoracolumbar Fascia,[Thoracic Region : Abdominal & Core Region]
141,FASCIA,Lumbar & Lower Back Region,Right,Thoracolumbar Fascia,[Thoracic Region : Abdominal & Core Region]
142,FASCIA,Lumbar & Lower Back Region,Left,Lumbar Fascia,[]
143,FASCIA,Lumbar & Lower Back Region,Right,Lumbar Fascia,[]
144,FASCIA,Lumbar & Lower Back Region,Left,Iliolumbar Ligaments,[Pelvic Girdle & Hip Region]
145,FASCIA,Lumbar & Lower Back Region,Right,Iliolumbar Ligaments,[Pelvic Girdle & Hip Region]
146,MUSCLE,Pelvic Girdle & Hip Region,Left,Iliacus,[Abdominal & Core Region]
147,MUSCLE,Pelvic Girdle & Hip Region,Right,Iliacus,[Abdominal & Core Region]
148,MUSCLE,Pelvic Girdle & Hip Region,Left,Rectus Femoris,[Thigh (Knee) Region]
149,MUSCLE,Pelvic Girdle & Hip Region,Right,Rectus Femoris,[Thigh (Knee) Region]
150,MUSCLE,Pelvic Girdle & Hip Region,Left,Tensor Fasciae Latae,[]
151,MUSCLE,Pelvic Girdle & Hip Region,Right,Tensor Fasciae Latae,[]
152,MUSCLE,Pelvic Girdle & Hip Region,Left,Gluteus Maximus,[]
153,MUSCLE,Pelvic Girdle & Hip Region,Right,Gluteus Maximus,[]
154,MUSCLE,Pelvic Girdle & Hip Region,Left,Biceps Femoris,[Thigh (Knee) Region]
155,MUSCLE,Pelvic Girdle & Hip Region,Right,Biceps Femoris,[Thigh (Knee) Region]
156,MUSCLE,Pelvic Girdle & Hip Region,Left,Semitendinosus,[Thigh (Knee) Region]
157,MUSCLE,Pelvic Girdle & Hip Region,Right,Semitendinosus,[Thigh (Knee) Region]
158,MUSCLE,Pelvic Girdle & Hip Region,Left,Semimembranosus,[Thigh (Knee) Region]
159,MUSCLE,Pelvic Girdle & Hip Region,Right,Semimembranosus,[Thigh (Knee) Region]
160,MUSCLE,Pelvic Girdle & Hip Region,Left,Gluteus Medius,[]
161,MUSCLE,Pelvic Girdle & Hip Region,Right,Gluteus Medius,[]
162,MUSCLE,Pelvic Girdle & Hip Region,Left,Gluteus Minimus,[]
163,MUSCLE,Pelvic Girdle & Hip Region,Right,Gluteus Minimus,[]
164,MUSCLE,Pelvic Girdle & Hip Region,Left,Adductor Longus,[]
165,MUSCLE,Pelvic Girdle & Hip Region,Right,Adductor Longus,[]
166,MUSCLE,Pelvic Girdle & Hip Region,Left,Adductor Brevis,[]
167,MUSCLE,Pelvic Girdle & Hip Region,Right,Adductor Brevis,[]
168,MUSCLE,Pelvic Girdle & Hip Region,Left,Adductor Magnus,[]
169,MUSCLE,Pelvic Girdle & Hip Region,Right,Adductor Magnus,[]
170,MUSCLE,Pelvic Girdle & Hip Region,Left,Pectineus,[]
171,MUSCLE,Pelvic Girdle & Hip Region,Right,Pectineus,[]
172,MUSCLE,Pelvic Girdle & Hip Region,Left,Gracilis,[Thigh (Knee) Region]
173,MUSCLE,Pelvic Girdle & Hip Region,Right,Gracilis,[Thigh (Knee) Region]
174,MUSCLE,Pelvic Girdle & Hip Region,Left,Piriformis,[]
175,MUSCLE,Pelvic Girdle & Hip Region,Right,Piriformis,[]
176,MUSCLE,Pelvic Girdle & Hip Region,Left,Obturator Internus,[]
177,MUSCLE,Pelvic Girdle & Hip Region,Right,Obturator Internus,[]
178,MUSCLE,Pelvic Girdle & Hip Region,Left,Obturator Externus,[]
179,MUSCLE,Pelvic Girdle & Hip Region,Right,Obturator Externus,[]
180,MUSCLE,Pelvic Girdle & Hip Region,Left,Gemelli (Superior/Inferior),[]
181,MUSCLE,Pelvic Girdle & Hip Region,Right,Gemelli (Superior/Inferior),[]
182,MUSCLE,Pelvic Girdle & Hip Region,Left,Quadratus Femoris,[]
183,MUSCLE,Pelvic Girdle & Hip Region,Right,Quadratus Femoris,[]
184,FASCIA,Pelvic Girdle & Hip Region,Left,Iliotibial Band,[Thigh (Knee) Region]
185,FASCIA,Pelvic Girdle & Hip Region,Right,Iliotibial Band,[Thigh (Knee) Region]
186,FASCIA,Pelvic Girdle & Hip Region,Center,Pelvic Fascia,[]
187,FASCIA,Pelvic Girdle & Hip Region,Left,Inguinal Ligament,[]
188,FASCIA,Pelvic Girdle & Hip Region,Right,Inguinal Ligament,[]
189,MUSCLE,Thigh (Knee) Region,Left,Vastus Lateralis,[]
190,MUSCLE,Thigh (Knee) Region,Right,Vastus Lateralis,[]
191,MUSCLE,Thigh (Knee) Region,Left,Vastus Medialis (VMO),[]
192,MUSCLE,Thigh (Knee) Region,Right,Vastus Medialis (VMO),[]
193,MUSCLE,Thigh (Knee) Region,Left,Vastus Intermedius,[]
194,MUSCLE,Thigh (Knee) Region,Right,Vastus Intermedius,[]
195,MUSCLE,Thigh (Knee) Region,Left,Sartorius,[]
196,MUSCLE,Thigh (Knee) Region,Right,Sartorius,[]
197,MUSCLE,Thigh (Knee) Region,Left,Popliteus,[]
198,MUSCLE,Thigh (Knee) Region,Right,Popliteus,[]
199,FASCIA,Thigh (Knee) Region,Left,Fascia Lata,[]
200,FASCIA,Thigh (Knee) Region,Right,Fascia Lata,[]
201,FASCIA,Thigh (Knee) Region,Left,Patellar Retinaculum,[]
202,FASCIA,Thigh (Knee) Region,Right,Patellar Retinaculum,[]
203,MUSCLE,Lower Leg,Left,Gastrocnemius,[]
204,MUSCLE,Lower Leg,Right,Gastrocnemius,[]
205,MUSCLE,Lower Leg,Left,Soleus,[]
206,MUSCLE,Lower Leg,Right,Soleus,[]
207,MUSCLE,Lower Leg,Left,Tibialis Anterior,[]
208,MUSCLE,Lower Leg,Right,Tibialis Anterior,[]
209,MUSCLE,Lower Leg,Left,Tibialis Posterior,[Foot/Ankle]
210,MUSCLE,Lower Leg,Right,Tibialis Posterior,[Foot/Ankle]
211,MUSCLE,Lower Leg,Left,Peroneus (Fibularis) Longus,[Foot/Ankle]
212,MUSCLE,Lower Leg,Right,Peroneus (Fibularis) Longus,[Foot/Ankle]
213,MUSCLE,Lower Leg,Left,Peroneus (Fibularis) Brevis,[]
214,MUSCLE,Lower Leg,Right,Peroneus (Fibularis) Brevis,[]
215,MUSCLE,Lower Leg,Left,Flexor Digitorum Longus,[]
216,MUSCLE,Lower Leg,Right,Flexor Digitorum Longus,[]
217,MUSCLE,Lower Leg,Left,Flexor Hallucis Longus,[Foot/Ankle]
218,MUSCLE,Lower Leg,Right,Flexor Hallucis Longus,[Foot/Ankle]
219,MUSCLE,Lower Leg,Left,Extensor Digitorum Longus,[]
220,MUSCLE,Lower Leg,Right,Extensor Digitorum Longus,[]
221,MUSCLE,Lower Leg,Left,Extensor Hallucis Longus,[Foot/Ankle]
222,MUSCLE,Lower Leg,Right,Extensor Hallucis Longus,[Foot/Ankle]
223,FASCIA,Lower Leg,Left,Crural Fascia,[]
224,FASCIA,Lower Leg,Right,Crural Fascia,[]
225,FASCIA,Lower Leg,Left,Achilles Tendon,[]
226,FASCIA,Lower Leg,Right,Achilles Tendon,[]
227,MUSCLE,Foot/Ankle,Left,Interossei (Foot),[]
228,MUSCLE,Foot/Ankle,Right,Interossei (Foot),[]
229,MUSCLE,Foot/Ankle,Left,Lumbricals (Foot),[]
230,MUSCLE,Foot/Ankle,Right,Lumbricals (Foot),[]
231,MUSCLE,Foot/Ankle,Left,Flexor Digiti Minimi Brevis,[]
232,MUSCLE,Foot/Ankle,Right,Flexor Digiti Minimi Brevis,[]
233,MUSCLE,Foot/Ankle,Left,Flexor Hallucis Brevis,[]
234,MUSCLE,Foot/Ankle,Right,Flexor Hallucis Brevis,[]
235,MUSCLE,Foot/Ankle,Left,Extensor Hallucis Brevis,[]
236,MUSCLE,Foot/Ankle,Right,Extensor Hallucis Brevis,[]
237,MUSCLE,Foot/Ankle,Left,Flexor Digitorum Brevis,[]
238,MUSCLE,Foot/Ankle,Right,Flexor Digitorum Brevis,[]
239,MUSCLE,Foot/Ankle,Left,Extensor Digitorum Brevis,[]
240,MUSCLE,Foot/Ankle,Right,Extensor Digitorum Brevis,[]
241,FASCIA,Foot/Ankle,Left,Plantar Fascia (Plantar Aponeurosis),[]
242,FASCIA,Foot/Ankle,Left,Flexor Retinaculum,[]
243,FASCIA,Foot/Ankle,Right,Flexor Retinaculum,[]
244,FASCIA,Foot/Ankle,Left,Extensor Retinaculum,[]
245,FASCIA,Foot/Ankle,Right,Extensor Retinaculum,[]
246,FASCIA,Foot/Ankle,Left,Peroneal Retinaculum,[]
247,FASCIA,Foot/Ankle,Right,Peroneal Retinaculum,[]
"""
    
    try:
        connection = create_connection()
        print("Connected to muscledB database.")
        
        # Create the Muscles table.
        create_muscles_table(connection)
        print("Muscles table created (if not already existing).")
        
        # Process and insert the CSV data.
        process_csv_data(connection, csv_data)
        print("All muscle and fascia records have been inserted.")
    
    except Error as e:
        print("Error:", e)
    
    finally:
        if connection.is_connected():
            connection.close()
            print("MySQL connection closed.")

if __name__ == "__main__":
    main()
