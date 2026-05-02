# Inventory UI Improvement Plan
Track progress by marking [x] when complete.

## Completed Steps
- [x] Analyzed current inventory_module.py, services, repos, data flow
- [x] User approved detailed improvement plan
- [x] Created this updated TODO.md
- [x] Step 1: Added filter toolbar (category/stock dropdowns), enhanced refresh_data with client-side filtering
- [x] Step 2: Implemented sortable column headers (click to sort asc/desc), Step 3: Pagination (25/page, prev/next, page info)
- [x] Step 4: Low stock alerts (banner + popup with top 20 + bulk restock)
- [x] Step 5: Export filtered CSV button
- [x] Step 6: Enhanced history popup with matplotlib tabbed view (table + stock trend chart)

## Implementation Steps (Logical Order)
1. [ ] Add filter toolbar to inventory_module.py: Category dropdown (populate from service.get_categories), stock status filters (All / Low / Critical), enhanced search (name/category/stock)
2. [ ] Implement sortable column headers on treeview (client-side sort by clicked column, handle numeric/text)
3. [ ] Add pagination controls below treeview (prev/next/page size, client-side slicing on filtered data, default page 25)
4. [ ] Create prominent low-stock alerts section (above treeview: badge/count, expandable list of critical items with quick restock button)
5. [ ] Add 'Export Filtered to CSV' button (use csv module, write filtered data with headers)
6. [ ] Enhance show_stock_history popup: Add matplotlib bar chart for IN/OUT/ADJUST movements
7. [ ] Add bulk price adjustment preview dialog (show count affected, sample before/after prices, confirm)
8. [ ] UI polish: Color-code stock levels in treeview/tags (green>min*2, yellow>min, red<=min), stock progress bars in details
9. [ ] Responsive layout: Use grid weights, scrollable panels, mobile-friendly spacing
10. [ ] Test: Run app, navigate to Inventory, verify all features (filters/sort/pag/export/charts/bulk), check performance with 100+ products

## Follow-up Steps After Edits
- Install matplotlib: `pip install matplotlib`
- Test command: `python main.py`
- No service/repo changes needed (client-side UI enhancements)

## Notes
- Maintain data flow: UI collects -> service validates -> repo/DB
- All changes client-side except service calls for data/history
- Backup inventory_module.py before edits
