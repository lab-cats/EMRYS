# Shared awk helper predicates used by multiple Step 09 CMH validation scripts.
function absolute(v){ return v < 0 ? -v : v }
function is_number(v){ return v ~ /^-?([0-9]+([.][0-9]*)?|[.][0-9]+)([eE][+-]?[0-9]+)?$/ }
function is_nonnegative_number(v){ return is_number(v) && v + 0 >= 0 }
function is_nonnegative_integer(v){ return v ~ /^(0|[1-9][0-9]*)$/ }
function is_fraction(v){ return is_number(v) && v + 0 >= 0 && v + 0 <= 1 }
function is_odds_ratio(v){ return v == "Inf" || is_nonnegative_number(v) }
function odds_ratio_above(v, t){ return v == "Inf" || v + 0 > t + 0 }
function odds_ratio_below(v, t){ return v != "Inf" && v + 0 < 1 / (t + 0) }
