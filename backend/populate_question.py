import os
import django

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from apps.content.models import Subject, Topic, Question
from django.core.exceptions import ValidationError
import random

def generate_questions():
    # Subjects and topics (from previous population)
    subjects = Subject.objects.all()
    difficulties = ['E', 'M', 'H']
    question_count_per_subject = 15

    # Complete question data with 15 questions per subject (5 topics × 3 difficulties)
    question_data = {
        "Mathematics": {
            "Algebra": [
                ("E", "What is 2 + 3?", {"A": "4", "B": "5", "C": "6", "D": "7"}, "B"),
                ("M", "Solve for x: 2x + 3 = 7", {"A": "2", "B": "3", "C": "4", "D": "5"}, "A"),
                ("H", "Find x if x² - 5x + 6 = 0", {"A": "2, 3", "B": "1, 4", "C": "2, 4", "D": "3, 5"}, "A"),
                ("E", "What is 5 - 2?", {"A": "2", "B": "3", "C": "4", "D": "7"}, "B"),
                ("M", "Solve for y: 3y - 4 = 5", {"A": "1", "B": "2", "C": "3", "D": "4"}, "C"),
                ("H", "Solve x² - 4x + 4 = 0", {"A": "2", "B": "1", "C": "0", "D": "4"}, "A"),
            ],
            "Calculus": [
                ("E", "What is the derivative of x²?", {"A": "2x", "B": "x", "C": "2", "D": "x³"}, "A"),
                ("M", "Integrate x dx from 0 to 2", {"A": "1", "B": "2", "C": "3", "D": "4"}, "B"),
                ("H", "Evaluate ∫(1/x) dx from 1 to e", {"A": "1", "B": "2", "C": "e", "D": "ln(e)"}, "A"),
                ("E", "What is the derivative of x?", {"A": "1", "B": "x", "C": "0", "D": "2x"}, "A"),
                ("M", "Integrate x² dx from 0 to 1", {"A": "0.5", "B": "1", "C": "0.33", "D": "2"}, "C"),
                ("H", "Find ∫(2x + 1) dx", {"A": "x² + x", "B": "x² + x + C", "C": "2x²", "D": "x + C"}, "B"),
            ],
            "Geometry": [
                ("E", "What is the sum of angles in a triangle?", {"A": "90°", "B": "180°", "C": "270°", "D": "360°"}, "B"),
                ("M", "Calculate the area of a circle with radius 2", {"A": "4π", "B": "2π", "C": "6π", "D": "8π"}, "A"),
                ("H", "Prove the Pythagorean theorem", {"A": "a² + b² = c²", "B": "a + b = c", "C": "a² - b² = c", "D": "a³ = c"}, "A"),
                ("E", "How many sides does a pentagon have?", {"A": "4", "B": "5", "C": "6", "D": "7"}, "B"),
                ("M", "Find the perimeter of a square with side 3", {"A": "9", "B": "12", "C": "6", "D": "15"}, "B"),
                ("H", "Determine if a triangle with sides 3, 4, 5 is right-angled", {"A": "Yes", "B": "No", "C": "Maybe", "D": "Unknown"}, "A"),
            ],
            "Trigonometry": [
                ("E", "What is sin(0°)?", {"A": "0", "B": "1", "C": "-1", "D": "0.5"}, "A"),
                ("M", "Find sin(30°)", {"A": "0.5", "B": "1", "C": "0", "D": "0.707"}, "A"),
                ("H", "Solve sin(x) = 0.5 for x in [0, 2π]", {"A": "π/6, 5π/6", "B": "π/3, 2π/3", "C": "π/4, 3π/4", "D": "0, π"}, "A"),
                ("E", "What is cos(90°)?", {"A": "0", "B": "1", "C": "-1", "D": "0.5"}, "A"),
                ("M", "Find tan(45°)", {"A": "0", "B": "1", "C": "0.707", "D": "-1"}, "B"),
                ("H", "Prove sin²(x) + cos²(x) = 1", {"A": "True", "B": "False", "C": "Sometimes", "D": "Never"}, "A"),
            ],
            "Statistics": [
                ("E", "What is the average of 2, 4, 6?", {"A": "3", "B": "4", "C": "5", "D": "6"}, "B"),
                ("M", "Find the median of 1, 3, 2, 4, 5", {"A": "2", "B": "3", "C": "4", "D": "5"}, "B"),
                ("H", "Calculate the standard deviation for 2, 4, 6", {"A": "1.63", "B": "2", "C": "1.41", "D": "0"}, "C"),
                ("E", "What is the mode of 1, 2, 2, 3?", {"A": "1", "B": "2", "C": "3", "D": "None"}, "B"),
                ("M", "Find the mean of 10, 20, 30, 40", {"A": "20", "B": "25", "C": "30", "D": "35"}, "B"),
                ("H", "Explain the concept of variance", {"A": "Average squared deviation", "B": "Mean difference", "C": "Total sum", "D": "Range"}, "A"),
            ],
        },
        "Physics": {
            "Mechanics": [
                ("E", "What is the unit of force?", {"A": "kg", "B": "N", "C": "m/s", "D": "J"}, "B"),
                ("M", "Calculate acceleration if F=10N, m=2kg", {"A": "2 m/s²", "B": "5 m/s²", "C": "10 m/s²", "D": "20 m/s²"}, "B"),
                ("H", "Derive the work-energy theorem", {"A": "W=Fd", "B": "KE=½mv²", "C": "W=ΔKE", "D": "F=ma"}, "C"),
                ("E", "What is weight?", {"A": "Mass", "B": "mg", "C": "Force", "D": "Velocity"}, "B"),
                ("M", "Find velocity if a=2 m/s², t=5s, u=0", {"A": "5 m/s", "B": "10 m/s", "C": "15 m/s", "D": "20 m/s"}, "B"),
                ("H", "Explain Newton’s Third Law", {"A": "Action=Reaction", "B": "F=ma", "C": "v=at", "D": "Energy conservation"}, "A"),
            ],
            "Electricity": [
                ("E", "What flows in a wire?", {"A": "Light", "B": "Electrons", "C": "Protons", "D": "Neutrons"}, "B"),
                ("M", "What is Ohm’s Law?", {"A": "V=IR", "B": "I=V/R", "C": "R=V/I", "D": "All"}, "A"),
                ("H", "Derive the power in a circuit", {"A": "P=IV", "B": "P=V²/R", "C": "P=I²R", "D": "All"}, "D"),
                ("E", "What is a battery?", {"A": "Energy source", "B": "Wire", "C": "Switch", "D": "Resistor"}, "A"),
                ("M", "Calculate current if V=10V, R=5Ω", {"A": "1A", "B": "2A", "C": "5A", "D": "10A"}, "B"),
                ("H", "Explain Kirchhoff’s Current Law", {"A": "Sum of currents = 0", "B": "Voltage drops", "C": "Power loss", "D": "Resistance"}, "A"),
            ],
            "Magnetism": [
                ("E", "What attracts iron?", {"A": "Wood", "B": "Magnet", "C": "Plastic", "D": "Glass"}, "B"),
                ("M", "What is a magnetic field?", {"A": "Electric force", "B": "Region of force", "C": "Light wave", "D": "Sound"}, "B"),
                ("H", "Derive the force on a current in a magnetic field", {"A": "F=ILB", "B": "F=qvB", "C": "F=ma", "D": "F=IR"}, "A"),
                ("E", "What is a north pole?", {"A": "Repels north", "B": "Attracts south", "C": "Repels south", "D": "No effect"}, "B"),
                ("M", "Find the field strength if F=2N, I=1A, L=2m", {"A": "1T", "B": "2T", "C": "0.5T", "D": "4T"}, "A"),
                ("H", "Explain electromagnetic induction", {"A": "Motion induces current", "B": "Static charge", "C": "Heat loss", "D": "Light emission"}, "A"),
            ],
            "Thermodynamics": [
                ("E", "What is heat?", {"A": "Energy", "B": "Mass", "C": "Force", "D": "Speed"}, "A"),
                ("M", "What is the first law of thermodynamics?", {"A": "Energy conservation", "B": "Entropy increases", "C": "Heat loss", "D": "Work done"}, "A"),
                ("H", "Derive the Carnot efficiency", {"A": "1 - T_c/T_h", "B": "T_h/T_c", "C": "1 + T_c/T_h", "D": "T_c - T_h"}, "A"),
                ("E", "What is temperature?", {"A": "Heat measure", "B": "Mass", "C": "Volume", "D": "Density"}, "A"),
                ("M", "Calculate work done if P=2atm, V=2L", {"A": "4J", "B": "2J", "C": "6J", "D": "8J"}, "A"),
                ("H", "Explain the second law of thermodynamics", {"A": "Entropy increases", "B": "Energy decreases", "C": "Heat flows", "D": "Work stops"}, "A"),
            ],
            "Optics": [
                ("E", "What is light?", {"A": "Sound", "B": "Wave", "C": "Particle", "D": "Both B & C"}, "D"),
                ("M", "What is the law of reflection?", {"A": "Angle in = Angle out", "B": "Angle in > Angle out", "C": "Angle in = 0", "D": "Angle out = 90°"}, "A"),
                ("H", "Derive Snell’s Law", {"A": "n1sinθ1 = n2sinθ2", "B": "n1/n2 = sinθ2/sinθ1", "C": "n1θ1 = n2θ2", "D": "sinθ1 + sinθ2 = 1"}, "A"),
                ("E", "What is a mirror?", {"A": "Reflects light", "B": "Absorbs light", "C": "Refracts light", "D": "Emits light"}, "A"),
                ("M", "Find the focal length if u=10cm, v=20cm", {"A": "6.67cm", "B": "10cm", "C": "20cm", "D": "30cm"}, "A"),
                ("H", "Explain the principle of a lens", {"A": "Refraction bends light", "B": "Reflection occurs", "C": "Absorption happens", "D": "Diffusion spreads"}, "A"),
            ],
        },
        "Chemistry": {
            "Organic Chemistry": [
                ("E", "What is the simplest alkane?", {"A": "Ethane", "B": "Methane", "C": "Propane", "D": "Butane"}, "B"),
                ("M", "What functional group is in alcohols?", {"A": "-OH", "B": "-COOH", "C": "-CHO", "D": "-NH2"}, "A"),
                ("H", "Predict the product of C6H6 + Cl2 (UV light)", {"A": "C6H5Cl", "B": "C6H6Cl2", "C": "C6H12", "D": "C6H5OH"}, "A"),
                ("E", "What is an alkene?", {"A": "Single bond", "B": "Double bond", "C": "Triple bond", "D": "No bond"}, "B"),
                ("M", "Identify the product of CH4 + Cl2 (light)", {"A": "CH3Cl", "B": "C2H5Cl", "C": "CH2Cl2", "D": "CCl4"}, "A"),
                ("H", "Explain the mechanism of electrophilic addition", {"A": "π bond breaks", "B": "σ bond forms", "C": "H+ attacks", "D": "All"}, "D"),
            ],
            "Inorganic Chemistry": [
                ("E", "What is NaCl?", {"A": "Sugar", "B": "Salt", "C": "Acid", "D": "Base"}, "B"),
                ("M", "What is the oxidation state of Fe in Fe2O3?", {"A": "+2", "B": "+3", "C": "+4", "D": "+6"}, "B"),
                ("H", "Balance the equation: Fe + O2 → Fe2O3", {"A": "4Fe + 3O2 → 2Fe2O3", "B": "2Fe + O2 → Fe2O3", "C": "Fe + O2 → FeO", "D": "3Fe + 2O2 → Fe3O4"}, "A"),
                ("E", "What is water’s formula?", {"A": "H2O", "B": "CO2", "C": "NaCl", "D": "O2"}, "A"),
                ("M", "What is the charge of SO4?", {"A": "-1", "B": "-2", "C": "+1", "D": "+2"}, "B"),
                ("H", "Explain coordination compounds", {"A": "Metal-ligand complex", "B": "Ionic bond", "C": "Covalent bond", "D": "Free ions"}, "A"),
            ],
            "Physical Chemistry": [
                ("E", "What is pH?", {"A": "Acid measure", "B": "Base measure", "C": "Both", "D": "Neither"}, "C"),
                ("M", "What is the molarity of 1L with 2 moles?", {"A": "1M", "B": "2M", "C": "0.5M", "D": "4M"}, "B"),
                ("H", "Derive the ideal gas law", {"A": "PV=nRT", "B": "P=n/V", "C": "V=RT/P", "D": "P=RT/n"}, "A"),
                ("E", "What is a solution?", {"A": "Solid", "B": "Liquid mix", "C": "Gas", "D": "Element"}, "B"),
                ("M", "Calculate moles if mass=18g, MW=18", {"A": "0.5", "B": "1", "C": "2", "D": "3"}, "B"),
                ("H", "Explain Le Chatelier’s principle", {"A": "Equilibrium shifts", "B": "Reaction stops", "C": "Pressure drops", "D": "Heat increases"}, "A"),
            ],
            "Biochemistry": [
                ("E", "What is an enzyme?", {"A": "Protein", "B": "Carb", "C": "Lipid", "D": "Nucleic"}, "A"),
                ("M", "What does ATP provide?", {"A": "Energy", "B": "Water", "C": "Oxygen", "D": "Sugar"}, "A"),
                ("H", "Explain the Krebs cycle", {"A": "Energy production", "B": "Protein synthesis", "C": "DNA replication", "D": "Lipid breakdown"}, "A"),
                ("E", "What is DNA?", {"A": "Energy", "B": "Genetic code", "C": "Protein", "D": "Carb"}, "B"),
                ("M", "What is the role of hemoglobin?", {"A": "Oxygen transport", "B": "Sugar storage", "C": "Water balance", "D": "Heat"}, "A"),
                ("H", "Describe enzyme catalysis mechanism", {"A": "Lowers activation energy", "B": "Increases heat", "C": "Changes pH", "D": "Breaks bonds"}, "A"),
            ],
            "Analytical Chemistry": [
                ("E", "What is titration?", {"A": "Mixing", "B": "Volume measure", "C": "Acid-base test", "D": "Heat"}, "C"),
                ("M", "What indicator changes at pH 7?", {"A": "Litmus", "B": "Phenolphthalein", "C": "Methyl orange", "D": "Bromothymol"}, "A"),
                ("H", "Derive the Henderson-Hasselbalch equation", {"A": "pH = pKa + log([A-]/[HA])", "B": "pH = pKa - log([A-]/[HA])", "C": "pH = [H+]", "D": "pH = Ka"}, "A"),
                ("E", "What is a burette?", {"A": "Measure volume", "B": "Heat source", "C": "Stirrer", "D": "Filter"}, "A"),
                ("M", "Calculate pH if [H+]=10^-3", {"A": "2", "B": "3", "C": "4", "D": "5"}, "B"),
                ("H", "Explain chromatography", {"A": "Separates mixtures", "B": "Measures pH", "C": "Heats samples", "D": "Filters solids"}, "A"),
            ],
        },
        "Biology": {
            "Genetics": [
                ("E", "What carries genetic information?", {"A": "RNA", "B": "DNA", "C": "Protein", "D": "Lipid"}, "B"),
                ("M", "What is a dominant allele?", {"A": "Recessive trait", "B": "Expressed trait", "C": "Silent gene", "D": "Mutated gene"}, "B"),
                ("H", "Explain Mendel's Law of Segregation", {"A": "Alleles separate", "B": "Genes assort independently", "C": "Traits blend", "D": "DNA replicates"}, "A"),
                ("E", "What is a gene?", {"A": "Protein", "B": "DNA segment", "C": "RNA", "D": "Cell"}, "B"),
                ("M", "What is a Punnett square used for?", {"A": "Genotype prediction", "B": "Protein synthesis", "C": "Cell division", "D": "Energy"}, "A"),
                ("H", "Describe genetic linkage", {"A": "Genes on same chromosome", "B": "Random assortment", "C": "Mutation rate", "D": "DNA repair"}, "A"),
            ],
            "Ecology": [
                ("E", "What is an ecosystem?", {"A": "Animal group", "B": "Community + environment", "C": "Plant type", "D": "Water source"}, "B"),
                ("M", "What is a food chain?", {"A": "Energy flow", "B": "Water cycle", "C": "Plant growth", "D": "Animal migration"}, "A"),
                ("H", "Explain the carbon cycle", {"A": "CO2 exchange", "B": "Oxygen production", "C": "Nitrogen fixation", "D": "Water cycle"}, "A"),
                ("E", "What eats plants?", {"A": "Carnivores", "B": "Herbivores", "C": "Omnivores", "D": "Decomposers"}, "B"),
                ("M", "What is biodiversity?", {"A": "Species variety", "B": "Plant height", "C": "Water level", "D": "Soil type"}, "A"),
                ("H", "Analyze the impact of deforestation", {"A": "Habitat loss", "B": "CO2 increase", "C": "Both", "D": "Neither"}, "C"),
            ],
            "Cell Biology": [
                ("E", "What is a cell?", {"A": "Organ", "B": "Basic unit", "C": "Tissue", "D": "System"}, "B"),
                ("M", "What is the function of mitochondria?", {"A": "Energy", "B": "Storage", "C": "Transport", "D": "Protection"}, "A"),
                ("H", "Explain the process of mitosis", {"A": "Cell division", "B": "Protein synthesis", "C": "DNA replication", "D": "Energy use"}, "A"),
                ("E", "What is a nucleus?", {"A": "Energy", "B": "Control center", "C": "Storage", "D": "Wall"}, "B"),
                ("M", "What is osmosis?", {"A": "Water movement", "B": "Salt movement", "C": "Air flow", "D": "Heat"}, "A"),
                ("H", "Describe the role of ribosomes", {"A": "Protein synthesis", "B": "Energy production", "C": "DNA storage", "D": "Cell division"}, "A"),
            ],
            "Evolution": [
                ("E", "What is natural selection?", {"A": "Survival of fittest", "B": "Random change", "C": "Plant growth", "D": "Animal speed"}, "A"),
                ("M", "What is a species?", {"A": "Similar organisms", "B": "Different types", "C": "Plant only", "D": "Animal only"}, "A"),
                ("H", "Explain Darwin’s theory of evolution", {"A": "Natural selection", "B": "Mutation only", "C": "Artificial breeding", "D": "Random growth"}, "A"),
                ("E", "What is adaptation?", {"A": "Change to environment", "B": "Random mutation", "C": "Plant color", "D": "Animal size"}, "A"),
                ("M", "What is a fossil?", {"A": "Old remains", "B": "New plant", "C": "Water source", "D": "Rock type"}, "A"),
                ("H", "Analyze the evidence for evolution", {"A": "Fossils, DNA", "B": "Plants only", "C": "Animals only", "D": "Weather"}, "A"),
            ],
            "Human Anatomy": [
                ("E", "What is the heart?", {"A": "Muscle", "B": "Pump", "C": "Bone", "D": "Nerve"}, "B"),
                ("M", "What carries oxygen in blood?", {"A": "White cells", "B": "Red cells", "C": "Platelets", "D": "Plasma"}, "B"),
                ("H", "Explain the circulatory system", {"A": "Blood flow", "B": "Oxygen transport", "C": "Both", "D": "Neither"}, "C"),
                ("E", "What is a lung?", {"A": "Oxygen exchange", "B": "Food digest", "C": "Blood pump", "D": "Muscle"}, "A"),
                ("M", "What is the role of the liver?", {"A": "Detoxify", "B": "Pump blood", "C": "Breathe", "D": "Move"}, "A"),
                ("H", "Describe the nervous system function", {"A": "Signal transmission", "B": "Blood flow", "C": "Energy storage", "D": "Muscle growth"}, "A"),
            ],
        },
        "Computer Science": {
            "Programming": [
                ("E", "What does 'print()' do in Python?", {"A": "Input", "B": "Output", "C": "Loop", "D": "Define"}, "B"),
                ("M", "What is a function in programming?", {"A": "Variable", "B": "Reusable code", "C": "Loop", "D": "Class"}, "B"),
                ("H", "Write a recursive function for factorial", {"A": "n*(n-1)", "B": "if n=0:1 else n*f(n-1)", "C": "n+n", "D": "n!+1"}, "B"),
                ("E", "What is a variable?", {"A": "Function", "B": "Storage", "C": "Loop", "D": "Class"}, "B"),
                ("M", "What is a for loop?", {"A": "Iteration", "B": "Condition", "C": "Function", "D": "Variable"}, "A"),
                ("H", "Explain object-oriented programming", {"A": "Classes/objects", "B": "Loops only", "C": "Functions", "D": "Variables"}, "A"),
            ],
            "Data Structures": [
                ("E", "What is an array?", {"A": "List", "B": "Function", "C": "Loop", "D": "Class"}, "A"),
                ("M", "What is a stack?", {"A": "LIFO", "B": "FIFO", "C": "Random", "D": "Sorted"}, "A"),
                ("H", "Implement a binary search tree", {"A": "Balanced nodes", "B": "Linear search", "C": "Unsorted list", "D": "Random order"}, "A"),
                ("E", "What is a queue?", {"A": "FIFO", "B": "LIFO", "C": "Sorted", "D": "Random"}, "A"),
                ("M", "What is a linked list?", {"A": "Nodes connected", "B": "Array type", "C": "Function", "D": "Loop"}, "A"),
                ("H", "Explain hash table collision", {"A": "Key conflict", "B": "Memory full", "C": "Loop error", "D": "Input error"}, "A"),
            ],
            "Algorithms": [
                ("E", "What is sorting?", {"A": "Order data", "B": "Randomize", "C": "Delete", "D": "Add"}, "A"),
                ("M", "What is bubble sort?", {"A": "Adjacent swap", "B": "Random swap", "C": "Merge", "D": "Quick"}, "A"),
                ("H", "Analyze time complexity of quicksort", {"A": "O(n log n)", "B": "O(n²)", "C": "O(n)", "D": "O(1)"}, "A"),
                ("E", "What is searching?", {"A": "Find data", "B": "Sort data", "C": "Delete data", "D": "Add data"}, "A"),
                ("M", "What is binary search?", {"A": "Divide and conquer", "B": "Linear check", "C": "Random pick", "D": "Sort first"}, "A"),
                ("H", "Derive Dijkstra’s algorithm", {"A": "Shortest path", "B": "Longest path", "C": "Random walk", "D": "Cycle detection"}, "A"),
            ],
            "Databases": [
                ("E", "What is a database?", {"A": "Data storage", "B": "Function", "C": "Loop", "D": "Class"}, "A"),
                ("M", "What is SQL?", {"A": "Query language", "B": "Programming", "C": "Sorting", "D": "Networking"}, "A"),
                ("H", "Design a normalized database schema", {"A": "No redundancy", "B": "Duplicate data", "C": "Random tables", "D": "Single table"}, "A"),
                ("E", "What is a table?", {"A": "Data rows", "B": "Function", "C": "Loop", "D": "Class"}, "A"),
                ("M", "What is a primary key?", {"A": "Unique ID", "B": "Data value", "C": "Foreign key", "D": "Index"}, "A"),
                ("H", "Explain JOIN operation in SQL", {"A": "Combine tables", "B": "Sort data", "C": "Delete rows", "D": "Add columns"}, "A"),
            ],
            "Networking": [
                ("E", "What is an IP address?", {"A": "Network ID", "B": "Computer name", "C": "File path", "D": "Port"}, "A"),
                ("M", "What is TCP/IP?", {"A": "Protocol suite", "B": "File type", "C": "Hardware", "D": "Software"}, "A"),
                ("H", "Explain the OSI model", {"A": "7 layers", "B": "5 layers", "C": "3 layers", "D": "10 layers"}, "A"),
                ("E", "What is a router?", {"A": "Directs traffic", "B": "Stores data", "C": "Runs programs", "D": "Displays"}, "A"),
                ("M", "What is a subnet mask?", {"A": "Network division", "B": "IP address", "C": "Port number", "D": "Protocol"}, "A"),
                ("H", "Describe DHCP function", {"A": "IP assignment", "B": "Data encryption", "C": "Traffic control", "D": "File transfer"}, "A"),
            ],
        },
        "History": {
            "Ancient History": [
                ("E", "Who built the pyramids?", {"A": "Romans", "B": "Egyptians", "C": "Greeks", "D": "Persians"}, "B"),
                ("M", "When did the Roman Empire fall?", {"A": "476 AD", "B": "300 AD", "C": "600 AD", "D": "1000 AD"}, "A"),
                ("H", "Analyze the impact of Alexander's conquests", {"A": "Spread of Greek culture", "B": "End of trade", "C": "Isolation", "D": "No change"}, "A"),
                ("E", "What is a pharaoh?", {"A": "King", "B": "Priest", "C": "Soldier", "D": "Farmer"}, "A"),
                ("M", "When was the Great Wall started?", {"A": "221 BC", "B": "100 AD", "C": "500 BC", "D": "300 AD"}, "A"),
                ("H", "Explain the rise of Mesopotamia", {"A": "River valleys", "B": "Mountains", "C": "Deserts", "D": "Forests"}, "A"),
            ],
            "Medieval History": [
                ("E", "What is a castle?", {"A": "Fortress", "B": "House", "C": "Temple", "D": "Market"}, "A"),
                ("M", "Who signed the Magna Carta?", {"A": "King John", "B": "King Henry", "C": "King Richard", "D": "King Edward"}, "A"),
                ("H", "Analyze the impact of the Black Death", {"A": "Population decline", "B": "Trade increase", "C": "War start", "D": "Peace"}, "A"),
                ("E", "What is a knight?", {"A": "Soldier", "B": "Farmer", "C": "Priest", "D": "Merchant"}, "A"),
                ("M", "When was the Crusades?", {"A": "1095-1291", "B": "1000-1100", "C": "1300-1400", "D": "1500-1600"}, "A"),
                ("H", "Explain feudalism", {"A": "Land for service", "B": "Money trade", "C": "War only", "D": "Peace system"}, "A"),
            ],
            "Modern History": [
                ("E", "When was WWII?", {"A": "1939-1945", "B": "1914-1918", "C": "1900-1910", "D": "1950-1960"}, "A"),
                ("M", "Who was the leader of Nazi Germany?", {"A": "Hitler", "B": "Stalin", "C": "Churchill", "D": "Roosevelt"}, "A"),
                ("H", "Analyze the Cold War", {"A": "US vs USSR", "B": "WWII repeat", "C": "Trade war", "D": "Peace time"}, "A"),
                ("E", "What is a treaty?", {"A": "Peace agreement", "B": "War start", "C": "Trade deal", "D": "Land sale"}, "A"),
                ("M", "When was the Industrial Revolution?", {"A": "1750-1850", "B": "1800-1900", "C": "1600-1700", "D": "1900-2000"}, "A"),
                ("H", "Explain the impact of the Internet", {"A": "Global communication", "B": "Local trade", "C": "War increase", "D": "Isolation"}, "A"),
            ],
            "World Wars": [
                ("E", "What started WWI?", {"A": "Assassination", "B": "Trade", "C": "Disease", "D": "Weather"}, "A"),
                ("M", "What was the Treaty of Versailles?", {"A": "Peace deal", "B": "War start", "C": "Trade agreement", "D": "Alliance"}, "A"),
                ("H", "Analyze the causes of WWII", {"A": "Treaty failure", "B": "Economic boom", "C": "Peace treaties", "D": "Isolation"}, "A"),
                ("E", "What is a trench?", {"A": "War defense", "B": "River", "C": "Road", "D": "Bridge"}, "A"),
                ("M", "When was D-Day?", {"A": "1944", "B": "1940", "C": "1945", "D": "1939"}, "A"),
                ("H", "Explain the Holocaust", {"A": "Genocide", "B": "War strategy", "C": "Economic plan", "D": "Peace effort"}, "A"),
            ],
            "Civilizations": [
                ("E", "What is a civilization?", {"A": "Advanced society", "B": "Small village", "C": "Forest", "D": "River"}, "A"),
                ("M", "What was the Mayan known for?", {"A": "Pyramids", "B": "Castles", "C": "Ships", "D": "Roads"}, "A"),
                ("H", "Analyze the fall of the Roman Empire", {"A": "Invasions", "B": "Prosperity", "C": "Peace", "D": "Trade"}, "A"),
                ("E", "What is a city-state?", {"A": "Independent city", "B": "Large country", "C": "River town", "D": "Farm"}, "A"),
                ("M", "What was the Inca’s road system?", {"A": "Trade network", "B": "War path", "C": "River route", "D": "Farm land"}, "A"),
                ("H", "Explain the rise of Chinese dynasties", {"A": "Central rule", "B": "War only", "C": "Trade alone", "D": "Isolation"}, "A"),
            ],
        },
        "Geography": {
            "Physical Geography": [
                ("E", "What is the tallest mountain?", {"A": "K2", "B": "Everest", "C": "Kangchenjunga", "D": "Lhotse"}, "B"),
                ("M", "What causes erosion?", {"A": "Wind", "B": "Rain", "C": "Both", "D": "Neither"}, "C"),
                ("H", "Explain plate tectonics theory", {"A": "Earth's crust moves", "B": "Weather patterns", "C": "Ocean currents", "D": "Volcano formation"}, "A"),
                ("E", "What is a river?", {"A": "Water flow", "B": "Mountain", "C": "Forest", "D": "Desert"}, "A"),
                ("M", "What forms a valley?", {"A": "Erosion", "B": "Volcano", "C": "Earthquake", "D": "Rain"}, "A"),
                ("H", "Describe the water cycle", {"A": "Evaporation to rain", "B": "Rain to wind", "C": "Heat to cold", "D": "Earth movement"}, "A"),
            ],
            "Human Geography": [
                ("E", "What is a city?", {"A": "Large town", "B": "Small village", "C": "River", "D": "Mountain"}, "A"),
                ("M", "What is population density?", {"A": "People per area", "B": "City size", "C": "Road length", "D": "Water"}, "A"),
                ("H", "Analyze urbanization trends", {"A": "City growth", "B": "Rural increase", "C": "Forest expansion", "D": "Desert spread"}, "A"),
                ("E", "What is a country?", {"A": "Nation", "B": "City", "C": "River", "D": "Mountain"}, "A"),
                ("M", "What is migration?", {"A": "People movement", "B": "Water flow", "C": "Plant growth", "D": "Animal hunt"}, "A"),
                ("H", "Explain cultural diffusion", {"A": "Idea spread", "B": "Water movement", "C": "Soil erosion", "D": "Wind"}, "A"),
            ],
            "Climatology": [
                ("E", "What is weather?", {"A": "Daily condition", "B": "Long-term", "C": "Soil type", "D": "River"}, "A"),
                ("M", "What causes rain?", {"A": "Condensation", "B": "Evaporation", "C": "Both", "D": "Neither"}, "C"),
                ("H", "Explain the greenhouse effect", {"A": "Heat trapping", "B": "Cold increase", "C": "Rain formation", "D": "Wind"}, "A"),
                ("E", "What is a storm?", {"A": "Strong weather", "B": "Calm day", "C": "River flow", "D": "Mountain"}, "A"),
                ("M", "What is climate change?", {"A": "Temperature shift", "B": "Rain increase", "C": "Wind change", "D": "Soil type"}, "A"),
                ("H", "Analyze El Niño impact", {"A": "Weather disruption", "B": "Rain increase", "C": "Wind only", "D": "Heat"}, "A"),
            ],
            "Geomorphology": [
                ("E", "What is a hill?", {"A": "Small mountain", "B": "River", "C": "Forest", "D": "Desert"}, "A"),
                ("M", "What shapes a canyon?", {"A": "Erosion", "B": "Volcano", "C": "Rain", "D": "Wind"}, "A"),
                ("H", "Explain the formation of deltas", {"A": "Sediment deposit", "B": "Volcanic eruption", "C": "Earthquake", "D": "Rain"}, "A"),
                ("E", "What is a plateau?", {"A": "Flat highland", "B": "River", "C": "Mountain", "D": "Valley"}, "A"),
                ("M", "What causes landslides?", {"A": "Gravity", "B": "Wind", "C": "Rain", "D": "Both A & C"}, "D"),
                ("H", "Describe glacial erosion", {"A": "Ice movement", "B": "Water flow", "C": "Wind action", "D": "Heat"}, "A"),
            ],
            "Cartography": [
                ("E", "What is a map?", {"A": "Land representation", "B": "Book", "C": "River", "D": "Mountain"}, "A"),
                ("M", "What is a scale on a map?", {"A": "Distance ratio", "B": "Color code", "C": "Height", "D": "Width"}, "A"),
                ("H", "Explain map projection", {"A": "Earth to flat", "B": "3D to 2D", "C": "Color change", "D": "Size adjust"}, "A"),
                ("E", "What is a legend?", {"A": "Key", "B": "Title", "C": "Scale", "D": "Border"}, "A"),
                ("M", "What is a contour line?", {"A": "Height level", "B": "River path", "C": "Road", "D": "City"}, "A"),
                ("H", "Analyze the Mercator projection", {"A": "Distorts size", "B": "Accurate shape", "C": "No distortion", "D": "Flat earth"}, "A"),
            ],
        },
        "English": {
            "Grammar": [
                ("E", "What is a noun?", {"A": "Action", "B": "Person/Thing", "C": "Description", "D": "Connection"}, "B"),
                ("M", "Identify the verb in 'She runs fast'", {"A": "She", "B": "Runs", "C": "Fast", "D": "None"}, "B"),
                ("H", "Analyze the sentence structure of 'Although tired, he finished'", {"A": "Simple", "B": "Compound", "C": "Complex", "D": "Fragment"}, "C"),
                ("E", "What is a verb?", {"A": "Action", "B": "Noun", "C": "Adjective", "D": "Adverb"}, "A"),
                ("M", "Identify the adjective in 'Big house'", {"A": "Big", "B": "House", "C": "In", "D": "None"}, "A"),
                ("H", "Explain passive voice", {"A": "Subject receives", "B": "Subject acts", "C": "No action", "D": "Adjective use"}, "A"),
            ],
            "Literature": [
                ("E", "Who wrote Romeo and Juliet?", {"A": "Shakespeare", "B": "Dickens", "C": "Austen", "D": "Twain"}, "A"),
                ("M", "What is a theme?", {"A": "Main idea", "B": "Character", "C": "Setting", "D": "Plot"}, "A"),
                ("H", "Analyze the symbolism in The Great Gatsby", {"A": "Green light", "B": "Red car", "C": "Blue sky", "D": "White house"}, "A"),
                ("E", "What is a novel?", {"A": "Long story", "B": "Short poem", "C": "Play", "D": "Essay"}, "A"),
                ("M", "What is a protagonist?", {"A": "Main character", "B": "Villain", "C": "Sidekick", "D": "Narrator"}, "A"),
                ("H", "Explain the structure of a sonnet", {"A": "14 lines", "B": "10 lines", "C": "20 lines", "D": "8 lines"}, "A"),
            ],
            "Writing Skills": [
                ("E", "What is a paragraph?", {"A": "Group of sentences", "B": "Single word", "C": "Title", "D": "Picture"}, "A"),
                ("M", "What is a thesis statement?", {"A": "Main argument", "B": "Topic sentence", "C": "Conclusion", "D": "Introduction"}, "A"),
                ("H", "Analyze the structure of an essay", {"A": "Intro, body, conclusion", "B": "Title, body", "C": "Intro, conclusion", "D": "Body only"}, "A"),
                ("E", "What is a sentence?", {"A": "Complete thought", "B": "Word", "C": "Phrase", "D": "Letter"}, "A"),
                ("M", "What is editing?", {"A": "Revise text", "B": "Write first", "C": "Read only", "D": "Delete all"}, "A"),
                ("H", "Explain persuasive writing techniques", {"A": "Emotion, logic", "B": "Random words", "C": "Colors", "D": "Pictures"}, "A"),
            ],
            "Vocabulary": [
                ("E", "What does 'happy' mean?", {"A": "Sad", "B": "Joyful", "C": "Angry", "D": "Tired"}, "B"),
                ("M", "What is a synonym for 'big'?", {"A": "Small", "B": "Large", "C": "Short", "D": "Thin"}, "B"),
                ("H", "Analyze the connotation of 'home'", {"A": "Warmth", "B": "Cold", "C": "Empty", "D": "Dark"}, "A"),
                ("E", "What does 'run' mean?", {"A": "Walk", "B": "Move fast", "C": "Sit", "D": "Sleep"}, "B"),
                ("M", "What is an antonym for 'hot'?", {"A": "Warm", "B": "Cold", "C": "Cool", "D": "Heat"}, "B"),
                ("H", "Explain the use of jargon", {"A": "Special terms", "B": "Common words", "C": "Random letters", "D": "Numbers"}, "A"),
            ],
            "Poetry": [
                ("E", "What is a poem?", {"A": "Verse", "B": "Story", "C": "Essay", "D": "Letter"}, "A"),
                ("M", "What is a rhyme?", {"A": "Sound match", "B": "Word order", "C": "Line length", "D": "Color"}, "A"),
                ("H", "Analyze the meter in 'iambic pentameter'", {"A": "Unstressed-stressed", "B": "Stressed only", "C": "Random", "D": "Unstressed"}, "A"),
                ("E", "What is a stanza?", {"A": "Poem section", "B": "Sentence", "C": "Title", "D": "Word"}, "A"),
                ("M", "What is alliteration?", {"A": "Repeated sounds", "B": "Rhyme", "C": "Meter", "D": "Stanza"}, "A"),
                ("H", "Explain the structure of a haiku", {"A": "5-7-5 syllables", "B": "10 lines", "C": "Free verse", "D": "4-4-4"}, "A"),
            ],
        },
        "Economics": {
            "Microeconomics": [
                ("E", "What is supply?", {"A": "Demand", "B": "Goods available", "C": "Price", "D": "Cost"}, "B"),
                ("M", "What affects elasticity of demand?", {"A": "Substitutes", "B": "Color", "C": "Weight", "D": "Shape"}, "A"),
                ("H", "Explain the concept of market equilibrium", {"A": "Supply=Demand", "B": "Price increases", "C": "Demand falls", "D": "Supply rises"}, "A"),
                ("E", "What is demand?", {"A": "Supply", "B": "Want for goods", "C": "Price", "D": "Cost"}, "B"),
                ("M", "What is a monopoly?", {"A": "Single seller", "B": "Many sellers", "C": "No sellers", "D": "Buyers only"}, "A"),
                ("H", "Analyze price elasticity", {"A": "Demand responsiveness", "B": "Supply change", "C": "Cost increase", "D": "Profit"}, "A"),
            ],
            "Macroeconomics": [
                ("E", "What is GDP?", {"A": "Total output", "B": "Single product", "C": "Cost", "D": "Profit"}, "A"),
                ("M", "What causes inflation?", {"A": "Rising prices", "B": "Falling prices", "C": "Stable prices", "D": "No change"}, "A"),
                ("H", "Explain the Phillips curve", {"A": "Inflation vs unemployment", "B": "GDP vs price", "C": "Demand vs supply", "D": "Cost vs profit"}, "A"),
                ("E", "What is unemployment?", {"A": "Jobless rate", "B": "Employment", "C": "Production", "D": "Trade"}, "A"),
                ("M", "What is fiscal policy?", {"A": "Government spending", "B": "Bank loans", "C": "Trade deals", "D": "Taxes"}, "A"),
                ("H", "Describe monetary policy", {"A": "Interest rate control", "B": "Tax adjustment", "C": "Trade regulation", "D": "Price fixing"}, "A"),
            ],
            "International Trade": [
                ("E", "What is export?", {"A": "Sell abroad", "B": "Buy local", "C": "Make goods", "D": "Use services"}, "A"),
                ("M", "What is a tariff?", {"A": "Tax on imports", "B": "Export fee", "C": "Local tax", "D": "Service charge"}, "A"),
                ("H", "Analyze the benefits of free trade", {"A": "Economic growth", "B": "Price rise", "C": "Job loss", "D": "Isolation"}, "A"),
                ("E", "What is import?", {"A": "Buy abroad", "B": "Sell local", "C": "Make goods", "D": "Use services"}, "A"),
                ("M", "What is a trade deficit?", {"A": "Imports > Exports", "B": "Exports > Imports", "C": "Equal trade", "D": "No trade"}, "A"),
                ("H", "Explain comparative advantage", {"A": "Efficient production", "B": "Cost increase", "C": "Trade ban", "D": "Price rise"}, "A"),
            ],
            "Development Economics": [
                ("E", "What is development?", {"A": "Economic growth", "B": "Population", "C": "Weather", "D": "Trade"}, "A"),
                ("M", "What is HDI?", {"A": "Human index", "B": "Trade measure", "C": "Price level", "D": "Job rate"}, "A"),
                ("H", "Analyze the impact of foreign aid", {"A": "Economic boost", "B": "Dependency", "C": "Both", "D": "Neither"}, "C"),
                ("E", "What is poverty?", {"A": "Low income", "B": "High wealth", "C": "Trade", "D": "Jobs"}, "A"),
                ("M", "What is infrastructure?", {"A": "Roads, power", "B": "Houses", "C": "Food", "D": "Water"}, "A"),
                ("H", "Explain the role of education in development", {"A": "Skill growth", "B": "Job loss", "C": "Trade drop", "D": "Cost rise"}, "A"),
            ],
            "Finance": [
                ("E", "What is money?", {"A": "Currency", "B": "Barter", "C": "Trade", "D": "Goods"}, "A"),
                ("M", "What is interest?", {"A": "Loan cost", "B": "Profit", "C": "Tax", "D": "Fee"}, "A"),
                ("H", "Analyze the stock market", {"A": "Share trading", "B": "Fixed income", "C": "Bank loans", "D": "Currency"}, "A"),
                ("E", "What is a bank?", {"A": "Money store", "B": "Shop", "C": "Factory", "D": "Farm"}, "A"),
                ("M", "What is a loan?", {"A": "Borrowed money", "B": "Saved money", "C": "Earned money", "D": "Invested"}, "A"),
                ("H", "Explain the role of central banks", {"A": "Money supply", "B": "Trade control", "C": "Job creation", "D": "Price fix"}, "A"),
            ],
        },
        "Art": {
            "Painting": [
                ("E", "What is watercolor?", {"A": "Oil paint", "B": "Water-based paint", "C": "Acrylic", "D": "Ink"}, "B"),
                ("M", "Who painted the Mona Lisa?", {"A": "Van Gogh", "B": "Da Vinci", "C": "Picasso", "D": "Monet"}, "B"),
                ("H", "Compare Renaissance and Modern painting styles", {"A": "Realism vs Abstract", "B": "Color vs Line", "C": "Both", "D": "Neither"}, "A"),
                ("E", "What is oil paint?", {"A": "Water-based", "B": "Oil-based", "C": "Acrylic", "D": "Ink"}, "B"),
                ("M", "Who painted Starry Night?", {"A": "Monet", "B": "Van Gogh", "C": "Da Vinci", "D": "Picasso"}, "B"),
                ("H", "Analyze the use of perspective in art", {"A": "Depth illusion", "B": "Color mix", "C": "Line draw", "D": "Shape"}, "A"),
            ],
            "Sculpture": [
                ("E", "What is a statue?", {"A": "3D art", "B": "Painting", "C": "Drawing", "D": "Photo"}, "A"),
                ("M", "Who sculpted David?", {"A": "Michelangelo", "B": "Rodin", "C": "Bernini", "D": "Donatello"}, "A"),
                ("H", "Analyze the technique of marble carving", {"A": "Chisel and hammer", "B": "Paint brush", "C": "Clay mold", "D": "Wood cut"}, "A"),
                ("E", "What is clay?", {"A": "Sculpture material", "B": "Paint", "C": "Paper", "D": "Ink"}, "A"),
                ("M", "Who created The Thinker?", {"A": "Rodin", "B": "Michelangelo", "C": "Da Vinci", "D": "Picasso"}, "A"),
                ("H", "Explain the evolution of sculpture", {"A": "Stone to metal", "B": "Paint to clay", "C": "Wood only", "D": "Paper"}, "A"),
            ],
            "Drawing": [
                ("E", "What is a sketch?", {"A": "Rough draft", "B": "Final art", "C": "Painting", "D": "Sculpture"}, "A"),
                ("M", "What is shading?", {"A": "Light and dark", "B": "Color mix", "C": "Line draw", "D": "Shape"}, "A"),
                ("H", "Analyze the use of proportion in drawing", {"A": "Size relation", "B": "Color use", "C": "Line style", "D": "Texture"}, "A"),
                ("E", "What is a pencil?", {"A": "Drawing tool", "B": "Paint", "C": "Clay", "D": "Ink"}, "A"),
                ("M", "What is perspective drawing?", {"A": "Depth effect", "B": "Flat image", "C": "Color mix", "D": "Line only"}, "A"),
                ("H", "Explain the technique of cross-hatching", {"A": "Overlapping lines", "B": "Single line", "C": "Color fill", "D": "Shading"}, "A"),
            ],
            "Art History": [
                ("E", "What is art history?", {"A": "Art past", "B": "Future art", "C": "Painting", "D": "Sculpture"}, "A"),
                ("M", "What period is the Renaissance?", {"A": "14-17th century", "B": "18th century", "C": "19th century", "D": "20th century"}, "A"),
                ("H", "Analyze the Baroque art movement", {"A": "Drama and emotion", "B": "Simple lines", "C": "Flat colors", "D": "Minimalism"}, "A"),
                ("E", "What is a movement?", {"A": "Art style", "B": "Painting", "C": "Sculpture", "D": "Drawing"}, "A"),
                ("M", "What is Impressionism?", {"A": "Light focus", "B": "Dark tones", "C": "Realism", "D": "Abstract"}, "A"),
                ("H", "Explain the impact of Cubism", {"A": "Fragmented forms", "B": "Realistic shapes", "C": "Single color", "D": "Line art"}, "A"),
            ],
            "Photography": [
                ("E", "What is a photo?", {"A": "Image", "B": "Painting", "C": "Sculpture", "D": "Drawing"}, "A"),
                ("M", "What is aperture?", {"A": "Light control", "B": "Focus", "C": "Zoom", "D": "Color"}, "A"),
                ("H", "Analyze the rule of thirds in photography", {"A": "Composition guide", "B": "Color balance", "C": "Light source", "D": "Focus point"}, "A"),
                ("E", "What is a camera?", {"A": "Image capture", "B": "Paint tool", "C": "Clay", "D": "Ink"}, "A"),
                ("M", "What is exposure?", {"A": "Light amount", "B": "Color mix", "C": "Focus", "D": "Zoom"}, "A"),
                ("H", "Explain the development of digital photography", {"A": "Pixel technology", "B": "Film only", "C": "Paint method", "D": "Sculpture"}, "A"),
            ],
        },
    }

    # Generate questions
    for subject in subjects:
        topics = subject.topic_set.all()
        for topic in topics:
            if topic.name in question_data.get(subject.name, {}):
                base_questions = question_data[subject.name][topic.name]
                for i in range(15):  # Ensure 15 questions per topic
                    if i < 5:
                        diff = 'E'
                    elif i < 10:
                        diff = 'M'
                    else:
                        diff = 'H'
                    # Use base questions and vary slightly
                    base_q = base_questions[i % len(base_questions)]
                    q_text = f"{base_q[0]} {topic.name} Q{i+1}: {base_q[1]} (Var {i//3+1})"
                    options = base_q[2]
                    correct = base_q[3]
                    metadata = {"explanation": f"Explanation for {topic.name} question {i+1} (Variation {i//3+1})"}
                    # Create question without topics first
                    question = Question(
                        question_text=q_text,
                        difficulty=diff,
                        created_by=None,
                        options=options,
                        correct_answer=correct,
                        metadata=metadata,
                        source="manual"
                    )
                    try:
                        question.clean()
                        question.save()
                        # Add topics after saving
                        question.topics.add(topic)
                    except ValidationError as e:
                        print(f"Error creating question for {subject.name} - {topic.name}: {e}")

    print(f"Generated {Question.objects.count()} questions across all subjects.")

if __name__ == "__main__":
    generate_questions()