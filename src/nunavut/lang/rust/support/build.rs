use std::io::Write;

fn main() -> std::io::Result<()> {
    let mut lib_rs = String::new();

    for entry in std::fs::read_dir("src/namespaces")? {
        let path = entry?.path();
        if path.is_dir() {
            let namespace = path.file_name().unwrap().to_str().unwrap();
            lib_rs.push_str(format!("pub mod {};\n", namespace).as_str());
        }
    }

    let mut out = std::fs::File::create("src/namespaces/mod.rs")?;
    out.write_all(lib_rs.as_bytes())?;
    Ok(())
}
