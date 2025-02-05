from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Session
from forms import VehicleForm, LoginForm, RegistrationForm, UpdateProfileForm
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt

# Inicializace Flask
app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Když se nepřihlášený uživatel pokusí přistoupit na chráněnou stránku

# Inicializace šifrování hesel
bcrypt = Bcrypt(app)

app.config['SECRET_KEY'] = '123'
app.config['SESSION_TYPE'] = 'filesystem'  # ✅ Nutné pro správné fungování session

# Připojení k databázi
app.config['SQLALCHEMY_DATABASE_URI'] = 'mssql+pyodbc://THE-BEAST\\SQLEXPRESS/FleetManagementTP?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Model databáze pro tabulku Users
class User(db.Model, UserMixin):
    __tablename__ = 'Users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

    # Flask-Login metoda, která vrací True, protože všichni uživatelé jsou aktivní
    @property
    def is_active(self):
        return True

# Model databáze pro tabulku Vehicles
class Vehicle(db.Model):
    __tablename__ = 'Vehicles'

    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)

# Automatické vytvoření tabulek při spuštění aplikace
with app.app_context():
    db.create_all()
    print("Tabulky byly vytvořeny (pokud již neexistovaly).")

# Profil uživatele endpoint
@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

# Funkce pro načtení uživatele podle ID
@login_manager.user_loader
def load_user(user_id):
    with db.session() as session:  # Použití session podle SQLAlchemy 2.0
        return session.get(User, int(user_id))

# Hlavní stránka
@app.route('/', methods=['GET'])
def welcome():
    flash("🚀 Flash zpráva funguje!", "success")
    return redirect(url_for('login'))

# Registrační endpoint (opravený pro SQLAlchemy 2.0)
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        with Session(db.engine) as session:
            # Kontrola, zda uživatel již existuje
            existing_user = session.scalars(
                db.select(User).filter_by(username=username)
            ).first()

            if existing_user:
                flash('Username already exists. Please choose a different one.', 'danger')
                return redirect(url_for('register'))

            # Šifrování hesla
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

            # Vytvoření nového uživatele
            new_user = User(username=username, password=hashed_password)
            session.add(new_user)
            session.commit()

            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))

    return render_template('register.html', form=form)

# Přihlašovací endpoint (opravený pro SQLAlchemy 2.0)
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        with Session(db.engine) as session:
            # Vyhledání uživatele podle uživatelského jména
            user = session.scalars(
                db.select(User).filter_by(username=username)
            ).first()

            if user and bcrypt.check_password_hash(user.password, password):
                login_user(user)
                flash('Logged in successfully!', 'success')
                return redirect(url_for('view_vehicles'))
            else:
                flash('Invalid username or password', 'danger')

    return render_template('login.html', form=form)

# Odhlašovací endpoint
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# Aktualizace profilu
@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = UpdateProfileForm()

    if form.validate_on_submit():
        print("✅ Formulář byl úspěšně odeslán!")  # Debugging

        with Session(db.engine) as session:
            user = session.get(User, current_user.id)
            if not user:
                flash("❌ User not found.", "danger")
                return redirect(url_for('profile'))

            # 🔹 Ujistíme se, že pokud je vyplněné heslo, musí být i potvrzení hesla
            if form.password.data:
                if not form.confirm_password.data:
                    flash('⚠️ Please confirm your new password.', 'warning')
                    print("🚨 Flash zpráva: ⚠️ Please confirm your new password.")
                    return render_template('edit_profile.html', form=form)

                if form.password.data != form.confirm_password.data:
                    flash('❌ Passwords do not match. Please try again.', 'danger')
                    print("🚨 Flash zpráva: ❌ Passwords do not match.")
                    return render_template('edit_profile.html', form=form)

                hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
                user.password = hashed_password

            user.username = form.username.data
            session.add(user)
            session.commit()
            flash('✅ Profile updated successfully! Please log in again.', 'success')
            print("🚨 Flash zpráva: ✅ Profile updated!")

        logout_user()
        return redirect(url_for('login'))

    return render_template('edit_profile.html', form=form)

# Smazání účtu
@app.route('/profile/delete', methods=['POST'])
@login_required
def delete_account():
    user_id = current_user.id
    logout_user()

    with db.session() as session:
        user = session.get(User, user_id)
        if user:
            session.delete(user)
            session.commit()

    flash('Your account has been deleted successfully!', 'info')
    return redirect(url_for('login'))


# Přidávání vozidel
@app.route('/add-vehicle', methods=['GET', 'POST'])
@login_required
def add_vehicle():
    form = VehicleForm()
    if form.validate_on_submit():
        brand = form.brand.data
        model = form.model.data
        year = form.year.data

        # Vytvoření nového vozidla a uložení do databáze
        new_vehicle = Vehicle(brand=brand, model=model, year=year)
        db.session.add(new_vehicle)
        db.session.commit()

        flash('Vehicle added successfully!', 'success')
        return redirect(url_for('add_vehicle'))

    return render_template('add_vehicle.html', form=form)

# Upravování vozidel
@app.route('/edit-vehicle/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_vehicle(id):
    # Vyhledání vozidla podle ID
    vehicle = Vehicle.query.get_or_404(id)

    # Inicializace formuláře s předvyplněnými daty
    form = VehicleForm(obj=vehicle)

    if form.validate_on_submit():
        # Aktualizace dat vozidla podle údajů z formuláře
        vehicle.brand = form.brand.data
        vehicle.model = form.model.data
        vehicle.year = form.year.data

        db.session.commit()
        flash('Vehicle updated successfully!', 'success')
        return redirect(url_for('view_vehicles'))

    return render_template('edit_vehicle.html', form=form, vehicle=vehicle)

# Odstraňování vozidel
@app.route('/delete-vehicle/<int:id>', methods=['POST'])
@login_required
def delete_vehicle(id):
    # Vyhledání vozidla podle ID
    vehicle = Vehicle.query.get_or_404(id)

    # Smazání vozidla z databáze
    db.session.delete(vehicle)
    db.session.commit()

    flash('Vehicle deleted successfully!', 'success')
    return redirect(url_for('view_vehicles'))

# Výpis vozidel
@app.route('/vehicles')
@login_required
def view_vehicles():
    sort_by = request.args.get('sort_by', 'id')  # Výchozí řazení podle ID
    order = request.args.get('order', 'asc')  # Výchozí směr řazení (vzestupně)

    if sort_by not in ['id', 'year']:
        sort_by = 'id'

    if order not in ['asc', 'desc']:
        order = 'asc'

    # Seřazení podle zvoleného sloupce a směru
    if order == 'asc':
        vehicles = Vehicle.query.order_by(db.asc(getattr(Vehicle, sort_by))).all()
    else:
        vehicles = Vehicle.query.order_by(db.desc(getattr(Vehicle, sort_by))).all()

    return render_template('vehicles.html', vehicles=vehicles, sort_by=sort_by, order=order)

@app.route('/debug-session')
def debug_session():
    print("📢 Aktuální session data:", session)
    return "Check terminal for session data."

if __name__ == '__main__':
    app.run(debug=True)
