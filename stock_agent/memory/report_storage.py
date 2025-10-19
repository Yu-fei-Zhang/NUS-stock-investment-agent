import mysql.connector
from mysql.connector import Error
from datetime import datetime

class StockReportDatabase:
    """
    stock_report_db
    stock_reports:
        - stock_code (VARCHAR): primary key
        - report_content (TEXT)
        - analysis_time (TIMESTAMP)
    """

    def __init__(self, host: str, user: str, password: str, database: str):
        """
        Initialize the database connection and ensure the table exists.
        """
        try:
            self.conn = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database
            )
            self.cursor = self.conn.cursor()
            self.create_table()
            print("Database connected successfully.")
        except Error as e:
            raise RuntimeError(f"Database connection failed: {e}")

    def create_table(self):
        """
        Create table if not exists.
        """
        create_table_query = """
            CREATE TABLE IF NOT EXISTS stock_reports (
                stock_code VARCHAR(20) PRIMARY KEY,
                report_content TEXT,
                analysis_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                 ON UPDATE CURRENT_TIMESTAMP
            )
        """
        self.cursor.execute(create_table_query)
        self.conn.commit()

    def add_report(self, stock_code: str, report_content: str) -> bool:
        """
        Insert a new stock report record.
        """
        insert_query = """
            INSERT INTO stock_reports (stock_code, report_content, analysis_time)
            VALUES (%s, %s, %s)
        """
        try:
            self.cursor.execute(insert_query, (stock_code, report_content, datetime.now()))
            self.conn.commit()
            print(f"Report added for stock_code={stock_code}")
            return True
        except mysql.connector.IntegrityError:
            print(f"Record already exists for stock_code={stock_code}")
            return False
        except Error as e:
            print(f"Failed to add report: {e}")
            return False

    def delete_report(self, stock_code: str) -> bool:
        """
        Delete a report by stock_code.
        """
        delete_query = "DELETE FROM stock_reports WHERE stock_code = %s"
        try:
            self.cursor.execute(delete_query, (stock_code,))
            self.conn.commit()
            if self.cursor.rowcount > 0:
                print(f"Report deleted for stock_code={stock_code}")
                return True
            else:
                print(f"No record found for stock_code={stock_code}")
                return False
        except Error as e:
            print(f"Failed to delete report: {e}")
            return False

    def update_report(self, stock_code: str, new_content: str) -> bool:
        """
        Update report content and analysis time.
        """
        update_query = """
            UPDATE stock_reports
            SET report_content = %s, analysis_time = %s
            WHERE stock_code = %s
        """
        try:
            self.cursor.execute(update_query, (new_content, datetime.now(), stock_code))
            self.conn.commit()
            if self.cursor.rowcount > 0:
                print(f"Report updated for stock_code={stock_code}")
                return True
            else:
                print(f"No record found for stock_code={stock_code}")
                return False
        except Error as e:
            print(f"Failed to update report: {e}")
            return False

    def get_report(self, stock_code: str) -> dict | None:
        """
        Retrieve a report by stock_code.
        """
        select_query = "SELECT stock_code, report_content, analysis_time FROM stock_reports WHERE stock_code = %s"
        try:
            self.cursor.execute(select_query, (stock_code,))
            row = self.cursor.fetchone()
            if row:
                report = {
                    "stock_code": row[0],
                    "report_content": row[1],
                    "analysis_time": row[2]
                }
                print(f"Retrieved report for {stock_code}")
                return report
            else:
                print(f"No report found for stock_code={stock_code}")
                return None
        except Error as e:
            print(f"Failed to fetch report: {e}")
            return None

    def close(self):
        """Close database connection."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("Database connection closed.")


if __name__ == "__main__":
    db = StockReportDatabase(
        host="localhost",
        user="root",
        password="",
        database="stock_report_db"
    )

    db.add_report("AAPL", "Apple Q4 analysis: stable growth, strong services revenue.")
    db.get_report("AAPL")
    db.update_report("AAPL", "Apple Q4 updated: better-than-expected iPhone sales.")
    db.delete_report("AAPL")
    db.close()