//! Settled kernels of Gerundelle in Rust. Each gives exactly what the Python it replaces gives, in the same order, so a run with it is
//! the same run, faster (the user, 2026-11-11: "try moving a settled kernel to Rust").
//!
//! embed: Understanding.embed (molecules.py), Abstract's subgraph matching. Every injective mapping of pattern nodes to graph nodes
//! that preserves each typed pattern edge (exact: same size and no extra graph edges among the image), in the same deterministic
//! order: pattern nodes taken most-connected first then by name, graph nodes tried in name order, stopping at the first (first) or at
//! `limit` mappings. Kinds are given precomputed (the Python calls pk/gk once per node, not once per try); a pattern node maps only
//! to a graph node of the same kind. Only the edges touching the node just assigned are checked: every other edge with both ends
//! mapped was checked when its later end was assigned, so the result is the Python's.

use pyo3::prelude::*;
use std::collections::{HashMap, HashSet};

struct Search {
    order: Vec<usize>,                  // pattern node ids, in the order they are assigned
    g_sorted: Vec<usize>,               // graph node ids, in name order (duplicates kept, as Python's sorted keeps them)
    incident: HashMap<usize, Vec<(usize, usize, usize)>>, // pattern node -> pattern edges touching it
    g_edges: HashSet<(usize, usize, usize)>,
    p_edges: HashSet<(usize, usize, usize)>,
    g_edge_list: Vec<(usize, usize, usize)>,
    p_kind: Option<HashMap<usize, Option<String>>>,
    g_kind: Option<HashMap<usize, Option<String>>>,
    exact: bool,
    first: bool,
    limit: usize,
    map: HashMap<usize, usize>,         // pattern node -> graph node (the Python's m)
    used: HashMap<usize, usize>,        // graph node -> times used now (the Python's `g in m.values()`)
    assigned: Vec<usize>,               // pattern nodes in the order assigned (the Python dict's key order)
    found: Vec<Vec<(usize, usize)>>,
}

impl Search {
    fn ok(&self, node: usize) -> bool {
        if let Some(edges) = self.incident.get(&node) {
            for &(r, a, b) in edges {
                if let (Some(&ma), Some(&mb)) = (self.map.get(&a), self.map.get(&b)) {
                    if !self.g_edges.contains(&(r, ma, mb)) {
                        return false;
                    }
                }
            }
        }
        true
    }

    fn go(&mut self, i: usize) {
        if (self.first && !self.found.is_empty()) || (self.limit > 0 && self.found.len() >= self.limit) {
            return;
        }
        if i == self.order.len() {
            if self.exact {
                let inv: HashMap<usize, usize> = self.map.iter().map(|(&k, &v)| (v, k)).collect();
                for &(r, a, b) in &self.g_edge_list {
                    if let (Some(&ia), Some(&ib)) = (inv.get(&a), inv.get(&b)) {
                        if !self.p_edges.contains(&(r, ia, ib)) {
                            return;
                        }
                    }
                }
            }
            self.found.push(self.assigned.iter().map(|&p| (p, self.map[&p])).collect());
            return;
        }
        let node = self.order[i];
        for gi in 0..self.g_sorted.len() {
            let g = self.g_sorted[gi];
            if self.used.get(&g).copied().unwrap_or(0) > 0 {
                continue;
            }
            if let (Some(pk), Some(gk)) = (&self.p_kind, &self.g_kind) {
                if pk.get(&node) != gk.get(&g) {
                    continue;
                }
            }
            self.map.insert(node, g);
            *self.used.entry(g).or_insert(0) += 1;
            self.assigned.push(node);
            if self.ok(node) {
                self.go(i + 1);
            }
            self.assigned.pop();
            *self.used.get_mut(&g).unwrap() -= 1;
            self.map.remove(&node);
        }
    }
}

#[pyfunction]
#[pyo3(signature = (p_nodes, p_edges, g_nodes, g_edges, exact, first, p_kinds, g_kinds, limit))]
#[allow(clippy::too_many_arguments)]
fn embed(
    p_nodes: Vec<String>,
    p_edges: Vec<(String, String, String)>,
    g_nodes: Vec<String>,
    g_edges: Vec<(String, String, String)>,
    exact: bool,
    first: bool,
    p_kinds: Option<Vec<Option<String>>>,
    g_kinds: Option<Vec<Option<String>>>,
    limit: usize,
) -> Vec<Vec<(String, String)>> {
    let mut ids: HashMap<String, usize> = HashMap::new();
    let mut names: Vec<String> = Vec::new();
    let mut id = |s: &String, ids: &mut HashMap<String, usize>, names: &mut Vec<String>| -> usize {
        if let Some(&i) = ids.get(s) {
            return i;
        }
        let i = names.len();
        names.push(s.clone());
        ids.insert(s.clone(), i);
        i
    };
    let p: Vec<usize> = p_nodes.iter().map(|s| id(s, &mut ids, &mut names)).collect();
    let g: Vec<usize> = g_nodes.iter().map(|s| id(s, &mut ids, &mut names)).collect();
    let pe: Vec<(usize, usize, usize)> = p_edges
        .iter()
        .map(|(r, a, b)| (id(r, &mut ids, &mut names), id(a, &mut ids, &mut names), id(b, &mut ids, &mut names)))
        .collect();
    let ge: Vec<(usize, usize, usize)> = g_edges
        .iter()
        .map(|(r, a, b)| (id(r, &mut ids, &mut names), id(a, &mut ids, &mut names), id(b, &mut ids, &mut names)))
        .collect();
    // exact needs as many graph nodes as pattern nodes: otherwise the Python finds nothing at any leaf
    if exact && g_nodes.len() != p_nodes.len() {
        return Vec::new();
    }
    // pattern nodes most-connected first, then by name (the Python: key=(-degree, name))
    let degree = |n: usize| pe.iter().filter(|&&(_, a, b)| a == n || b == n).count();
    let mut order = p.clone();
    order.sort_by(|&x, &y| degree(y).cmp(&degree(x)).then_with(|| names[x].cmp(&names[y])));
    let mut g_sorted = g.clone();
    g_sorted.sort_by(|&x, &y| names[x].cmp(&names[y]));
    let mut incident: HashMap<usize, Vec<(usize, usize, usize)>> = HashMap::new();
    for &(r, a, b) in &pe {
        incident.entry(a).or_default().push((r, a, b));
        if b != a {
            incident.entry(b).or_default().push((r, a, b));
        }
    }
    let p_kind = p_kinds.map(|ks| p.iter().copied().zip(ks).collect::<HashMap<usize, Option<String>>>());
    let g_kind = g_kinds.map(|ks| g.iter().copied().zip(ks).collect::<HashMap<usize, Option<String>>>());
    let mut s = Search {
        order,
        g_sorted,
        incident,
        g_edges: ge.iter().copied().collect(),
        p_edges: pe.iter().copied().collect(),
        g_edge_list: ge,
        p_kind,
        g_kind,
        exact,
        first,
        limit,
        map: HashMap::new(),
        used: HashMap::new(),
        assigned: Vec::new(),
        found: Vec::new(),
    };
    s.go(0);
    s.found
        .into_iter()
        .map(|m| m.into_iter().map(|(a, b)| (names[a].clone(), names[b].clone())).collect())
        .collect()
}

#[pymodule]
fn gerundelle_fast(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(embed, m)?)?;
    Ok(())
}
