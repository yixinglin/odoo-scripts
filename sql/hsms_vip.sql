select * from biz_customer;
select * from biz_customer_price ;
select * from biz_company where biz_company.del_flag = 0 and biz_company.parent_id=1;  # Groups
select * from biz_company where biz_company.del_flag = 0 and biz_company.parent_id>1;  # Companies

# 获取集团优惠价 2024.12.29。
select com.`level`, com.company_name as group_name, pd.article_number, pd.name as product_name, 
	cp.price as custom_price, pd.price_clsa as std_price_a, pd.price_clsb as std_price_b
	from biz_customer_price cp 
	left join biz_company com  on cp.customer_id = com.company_id
	left join biz_product pd on cp.product_id = pd.id
	where not com.del_flag and not pd.deleted and com.parent_id = 1
	order by com.company_name, pd.article_number;
