-- Дополнительные ограничения через ALTER
ALTER TABLE product
    ADD CONSTRAINT chk_product_time_select CHECK (time_to_select >= 0),
    ADD CONSTRAINT chk_product_time_ship CHECK (time_to_ship >= 0),
    ADD CONSTRAINT chk_product_max_amount CHECK (max_amount > 0),
    ADD CONSTRAINT chk_product_max_per_hand CHECK (max_amount > 0);

ALTER TABLE cell
    ADD CONSTRAINT fk_cell_product FOREIGN KEY (product_sku) REFERENCES product(sku) ON DELETE SET NULL,
    ADD CONSTRAINT fk_cell_zone FOREIGN KEY (zone_id) REFERENCES zone(zone_id) ON DELETE SET NULL,
    ADD CONSTRAINT chk_cell_count CHECK (count >= 0);

ALTER TABLE user_x_zone
    ADD CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES "user"(user_id) ON DELETE CASCADE,
    ADD CONSTRAINT fk_zone FOREIGN KEY (zone_id) REFERENCES zone(zone_id) ON DELETE CASCADE;

ALTER TABLE "user"
    ADD CONSTRAINT uq_user_phone UNIQUE (phone_number),
    ADD CONSTRAINT chk_user_phone_format CHECK (phone_number ~ '^\+?[0-9]+$');
