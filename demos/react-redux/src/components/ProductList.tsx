import React, { useEffect } from "react";
import { useAppDispatch, useAppSelector } from "../hooks";
import { fetchProducts, selectProducts, selectProductsStatus } from "../store/productsSlice";

interface Props {
  category: string;
}

export function ProductList({ category }: Props) {
  const dispatch = useAppDispatch();
  const products = useAppSelector(selectProducts);
  const status = useAppSelector(selectProductsStatus);

  useEffect(() => {
    if (status === "idle") {
      dispatch(fetchProducts(category));
    }
  }, [dispatch, category, status]);

  if (status === "loading") return <p>Loading...</p>;
  if (status === "failed") return <p>Error loading products.</p>;

  return (
    <ul>
      {products.map((p) => (
        <li key={p.id}>
          {p.name} — ${(p.priceCents / 100).toFixed(2)}
        </li>
      ))}
    </ul>
  );
}
