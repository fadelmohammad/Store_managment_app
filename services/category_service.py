class CategoryService:
    def __init__(self, category_repo):
        self.category_repo = category_repo

        if not (category_repo.conn):
            raise ValueError("Repositories must share the same DB connection")

    def get_categories(self):
        """fetches all categories"""
        return self.category_repo.get_all_flat()

    def get_category_path(self, category_id):
        return self.category_repo.get_path(category_id)

    def add_category(self, name, parent_id):
        self.category_repo.add(name, parent_id)

    def count_products_in_category(self, category_id):
        """Count products in the given category."""
        if not category_id:
            return 0

        if not hasattr(self.category_repo, 'count_products'):
            raise AttributeError("CategoryRepository must implement count_products(category_id)")

        return self.category_repo.count_products(category_id)

    def delete_category(self, category_id):
        try:
            if not category_id:
                raise ValueError("Category ID is required")

            categories = self.get_categories()
            category_exists = False
            category_name = ""
            
            for cat in categories:
                if cat.get("id") == category_id:
                    category_exists = True
                    category_name = cat.get("name", cat.get("path", "Unknown"))
                    break
            
            if not category_exists:
                raise ValueError(f"Category with id {category_id} not found")
            
 
            self.category_repo.delete(category_id)
            print(f" Category '{category_name}' (ID: {category_id}) deleted successfully")
            
        except Exception as e:
            print(f" Error in delete_category: {e}")
            raise

    def get_category_history(self, category_path):
        return self.category_repo.get_history(category_path)