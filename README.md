# Who Dunnit Bro?  
**Multi-Detective Crime Investigation App**

---

## FEATURES

- Secure login & registration  
- Multiple detectives with personal cases  
- Admin can assign cases  
- Add, edit, delete cases, clues, suspects  
- Solve cases with guilty suspect selection  
- Reports dashboard with charts  
- Easter egg after solving 3 cases  
- Dark detective theme + sound effects  

---

## LOGIN CREDENTIALS

| Username | Password | Role  |
|--------  |----------  |------ |        
| `admin`  | `admin123`| Admin | 
> New user? Go to **/register**

---

## SETUP

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup Database
```bash
mysql -u root -p < database/schema.sql
```
> Password: `san2427`

### 3. Run App
```bash
python app.py
```

### 4. Open in Browser
[http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## FILE STRUCTURE

```
C:.
│   .gitignore
│   app.py
│   config.py
│   README.md
│   requirements.txt
│
├───.dist
├───database
│       schema.sql
│
├───static
│   ├───css
│   │       style.css
│   │
│   ├───images
│   │       magnifying_glass.png
│   │
│   ├───js
│   │       main.js
│   │
│   └───sounds
│           case_closed.mp3
│
├───templates
│       add_case.html
│       add_clue.html
│       add_suspect.html
│       base.html
│       case_detail.html
│       dashboard.html
│       edit_case.html
│       edit_clue.html
│       edit_suspect.html
│       login.html
│       register.html
│       reports.html
│
├───utils
│   │   db.py
│   │
│   └───__pycache__
│           db.cpython-313.pyc
│
└───__pycache__
        app.cpython-313.pyc
        config.cpython-313.pyc
```
---
**Ready to solve crimes. Case open.**

