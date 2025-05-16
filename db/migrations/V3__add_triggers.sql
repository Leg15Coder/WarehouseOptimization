-- Если товар в ячейке исчезает (count = 0), product_sku обнуляется
CREATE OR REPLACE FUNCTION clear_sku_when_empty()
    RETURNS TRIGGER AS $$
BEGIN
    IF NEW.count = 0 THEN
        NEW.product_sku := NULL;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_clear_sku
    BEFORE UPDATE ON cell
    FOR EACH ROW
    WHEN (OLD.count <> 0 AND NEW.count = 0)
EXECUTE FUNCTION clear_sku_when_empty();
