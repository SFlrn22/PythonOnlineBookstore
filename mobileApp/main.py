from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import ObjectProperty
from kivymd.uix.scrollview import MDScrollView
import psycopg2
from werkzeug.security import check_password_hash, generate_password_hash
from kivymd.uix.list import OneLineListItem
from kivymd.uix.list import TwoLineListItem
conn = psycopg2.connect(database="", 
                        user = "", 
                        password = "", 
                        host = "", 
                        port = "")


cs = conn.cursor()


class MainApp(MDApp):

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "DeepPurple"
        self.icon = 'icon.ico'
        return Builder.load_file('main.kv')
    
    def register(self):
        username = self.root.ids.rusername.text
        email = self.root.ids.remail.text
        password = self.root.ids.rpassword.text
        confirmation = self.root.ids.rconfirmation.text
        if not username:    
            self.root.ids.rusername.error = True
        elif not email:
            self.root.ids.remail.error = True
        elif "@" not in email:
            self.root.ids.remail.error = True
        elif not password:    
            self.root.ids.rpassword.error = True
        elif not confirmation:
            self.root.ids.rconfirmation.error = True
        elif password != confirmation:
            self.root.ids.rconfirmation.error = True
            self.root.ids.rpassword.error = True
        else:
            query = "SELECT * from couriers WHERE username = %s"
            cs.execute(query, (username,))
            res = cs.fetchall()
            query2 = "SELECT * from couriers WHERE email = %s"
            cs.execute(query2, (email,))
            res2 = cs.fetchall()
            
            if len(res) != 0:
                self.root.ids.rusername.error = True
                self.root.ids.rusername.helper_text = "Username already exists"
            elif len(res2) != 0:
                self.root.ids.remail.error = True
                self.root.ids.remail.helper_text = "Email already exists"
            else:
                passh = generate_password_hash(password)
                insertq = "INSERT INTO couriers (username, password, email) VALUES (%s, %s, %s)"
                vals = (username, passh, email)
                cs.execute(insertq, vals)
                conn.commit()
                self.root.ids.logout.opacity = 0
                self.root.ids.logout.disabled = True
                self.root.ids.logout.height = 0

                self.root.ids.login.opacity = 1.0
                self.root.ids.login.disabled = True
                self.root.ids.login.height = 56.0

                self.root.ids.register.opacity = 1.0
                self.root.ids.register.disabled = True
                self.root.ids.register.height = 56.0

                
                self.root.ids.screen_manager.current = "login_screen"
    
    def login(self):
        username = self.root.ids.username.text
        password = self.root.ids.password.text
        if not username:    
            self.root.ids.username.error = True
        elif not password:    
            self.root.ids.password.error = True
        else:
            query = "SELECT * from couriers WHERE username = %s"
            cs.execute(query, (username,))
            res = cs.fetchall()
            if len(res) != 1:
                self.root.ids.username.error = True
                self.root.ids.username.helper_text = "Invalid username"
            elif not check_password_hash(res[0][2], password):
                self.root.ids.password.error = True
                self.root.ids.password.helper_text = "Invalid password"
            else:
                self.root.ids.login.opacity = 0
                self.root.ids.login.disabled = True
                self.root.ids.login.height = 0

                self.root.ids.register.opacity = 0
                self.root.ids.register.disabled = True
                self.root.ids.register.height = 0
                
                self.root.ids.logout.opacity = 1.0
                self.root.ids.logout.disabled = False
                self.root.ids.logout.height = 56.0

                self.root.ids.account.opacity = 1.0
                self.root.ids.account.disabled = False
                self.root.ids.account.height = 56.0

                self.root.ids.purchases.opacity = 1.0
                self.root.ids.purchases.disabled = False
                self.root.ids.purchases.height = 56.0

                self.root.ids.history.opacity = 1.0
                self.root.ids.history.disabled = False
                self.root.ids.history.height = 56.0
                
                self.root.ids.hdr.text = "{}\nMenu ".format(res[0][3])

                self.root.ids.account_label.text = "Hello, {}".format(res[0][1])
                self.root.ids.account_labelhdn.text = "{}".format(res[0][1])

                self.root.ids.screen_manager.current = "account_screen"
    
    def logout(self):
        self.root.ids.logout.opacity = 0
        self.root.ids.logout.disabled = True
        self.root.ids.logout.height = 0

        self.root.ids.account.opacity = 0
        self.root.ids.account.disabled = True
        self.root.ids.account.height = 0

        self.root.ids.purchases.opacity = 0
        self.root.ids.purchases.disabled = True
        self.root.ids.purchases.height = 0

        self.root.ids.history.opacity = 0
        self.root.ids.history.disabled = True
        self.root.ids.history.height = 0

        self.root.ids.login.opacity = 1.0
        self.root.ids.login.disabled = False
        self.root.ids.login.height = 56.0

        self.root.ids.register.opacity = 1.0
        self.root.ids.register.disabled = False
        self.root.ids.register.height = 56.0
    
    def account(self):
        self.root.ids.screen_manager.current = "account_screen"

    def refresh(self):
        self.root.ids.container.clear_widgets()
        self.root.ids.containerh.clear_widgets()
        
    def purchases(self):
        cuser = self.root.ids.account_labelhdn.text
        query = "SELECT * from couriers WHERE username = %s"
        cs.execute(query, (cuser,))
        res = cs.fetchall()
        idcourier = res[0][0]
        querry = "SELECT username, code FROM purch_join_view WHERE courier_id = %s and status = %s ORDER BY timeadd"
        cs.execute(querry, (idcourier, "in transit"))
        lst = cs.fetchall()
        for row in lst:
            self.root.ids.container.add_widget(
                OneLineListItem(text=f"Purchase code: {row[1]} client: {row[0]}", on_press= self.getit),
            )

        self.root.ids.screen_manager.current = "purchases_screen"

    def history(self):
        cuser = self.root.ids.account_labelhdn.text
        query = "SELECT * from couriers WHERE username = %s"
        cs.execute(query, (cuser,))
        res = cs.fetchall()
        idcourier = res[0][0]
        querry = "SELECT username, code FROM purch_join_view WHERE courier_id = %s ORDER BY timeadd"
        cs.execute(querry, (idcourier,))
        lst = cs.fetchall()
        for row in lst:
            self.root.ids.containerh.add_widget(
                OneLineListItem(text=f"Purchase code: {row[1]} client: {row[0]}", on_press= self.gethi),
            )

        self.root.ids.screen_manager.current = "history_screen"

    def getit(self, onelinelistitem):
        text = onelinelistitem.text
        fullt = text.partition("code: ")[2].split()
        code = fullt[0]
        name = text.partition("client: ")[2]
        q = "SELECT title FROM purch_view WHERE code = %s"
        cs.execute(q, (code,))
        books = cs.fetchall()
        q1 = "SELECT status FROM purch_view WHERE code = %s"
        cs.execute(q1, (code,))
        status = cs.fetchone()[0]
        listb = []
        for book in books:
            listb.append(book[0])
        string = '\n'.join(listb)
        self.root.ids.code_label.text = "Purchase code: {}".format(code)
        self.root.ids.user_label.text = "User: {}".format(name)
        self.root.ids.status_label.text = "Status: {}".format(status)
        self.root.ids.books_label.text = "{}".format(string)
        self.root.ids.screen_manager.current = "product_screen"

    def gethi(self, onelinelistitem):
        text = onelinelistitem.text
        fullt = text.partition("code: ")[2].split()
        code = fullt[0]
        name = text.partition("client: ")[2]
        q = "SELECT title FROM purch_view WHERE code = %s"
        cs.execute(q, (code,))
        books = cs.fetchall()
        q1 = "SELECT status FROM purch_view WHERE code = %s"
        cs.execute(q1, (code,))
        status = cs.fetchone()[0]
        listb = []
        for book in books:
            listb.append(book[0])
        string = '\n'.join(listb)
        self.root.ids.code_labelh.text = "Purchase code: {}".format(code)
        self.root.ids.user_labelh.text = "User: {}".format(name)
        self.root.ids.status_labelh.text = "Status: {}".format(status)
        self.root.ids.books_labelh.text = "{}".format(string)
        self.root.ids.screen_manager.current = "ph_screen"

    def delivered(self):
        code_text = self.root.ids.code_label.text
        code = code_text.partition("code: ")[2]
        q = "UPDATE purch_user SET delivered = %s WHERE code = %s"
        vals = ('yes', code)
        cs.execute(q, vals)
        conn.commit()
        self.root.ids.screen_manager.current = "purchases_screen"

if __name__ == '__main__':
    MainApp().run()