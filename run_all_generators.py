import os
import tools.Code_Exec as Code_Exec
import tools.MainFunctions as F2

# run all the generation scripts in the dataset to generate more images
########################################################################################################################################
# def run_all(main_dir,script_file="",new_dir_name="", run_samples=100):
#     for fff,sdr in enumerate(os.listdir(main_dir)):
#         dr = main_dir + "//" + sdr + "//"
#         code_file = dr + script_file
#         if not os.path.exists(code_file):
#             print("missing:",code_file)
#             continue
#         #*************TEMP*******************************************
#
#         if   not os.path.isdir(dr + "//new_textures_C") or os.listdir(dr + "//new_textures_C").__len__()<10: continue
#
#         #*********************************************************************************
#         with open(code_file,"r") as fl: code=fl.read()
#
#     #------------------run code on new samples-------------------------------
#         if run_samples and run_samples>0:
#             outdir = dr + "//"+new_dir_name+"//"
#             if os.path.exists(outdir) and len(os.listdir(outdir))>=run_samples:
#                  print(fff,")",outdir, " Finished")
#                  continue
#             print("Writing file to:", outdir)
#             testing_code_str = (
#                     "\nimport importlib\n" +
#                     "\nimport " + F2.path_to_import(code_file) + " as generate\n" +
#                     "\nimportlib.reload(generate)"
#                     "\noutdir = '" + outdir + "'" +
#                     "\ngenerate.generate_texture(outdir,num_samples="+str(run_samples)+")"
#             )
#             print("Running:\n"+testing_code_str)
#             try:#****
#                if outdir=='Textures_Final_100/endless_textures_Final_Selection_All_Good////Polyiamond_Substitution_Quilt//////new_textures_C////': continue
#                successed, captured_stdout, captured_stderr = Code_Exec.run_code(testing_code_str)
#             except:
#                 print("fail")
#                 continue
#             print("Finish writing file to:",outdir)
#             print("Succcess ",successed, captured_stdout, captured_stderr)
# if __name__ == "__main__":
#     main_dir = r"Scitextures//"
#     run_all(main_dir, script_file="generate.py",new_dir_name="//new_textures_100//",run_samples=100)
########################################################################################################################################
def run_all(main_dir,script_file,new_dir_name, run_command,num_samples=5):
    for fff,sdr in enumerate(os.listdir(main_dir)):
        dr = os.path.join(main_dir, sdr)
        code_file = os.path.join(dr,script_file)
        if not os.path.exists(code_file):
            print("missing:",code_file)
            continue

        #*********************************************************************************
      ###  with open(code_file,"r") as fl: code=fl.read()

    #------------------run code on new samples-------------------------------
        if num_samples and num_samples>0:
            outdir = os.path.join(dr,new_dir_name)
            if os.path.isdir(outdir) and len(os.listdir(outdir))>=num_samples:
                 print(fff,")",outdir, " Finished")
                 continue
            print("Writing file to:", outdir)
            module_name = script_file.replace(".py", "")

            testing_code_str = (
                    "\nimport importlib, os, sys"
                    "\nsubdir = '" + dr + "'"
                    "\nsys.path.insert(0, os.path.abspath(subdir))"
                    "\nimport " + module_name + " as generate"
                    "\nimportlib.reload(generate)"  # <--- THIS FORCES THE NEW FILE TO LOAD
                    "\noutdir = '" + outdir + "'"
                    "\ngenerate." + run_command
            )


            print("Running:\n"+testing_code_str)
            try:#****
               successed, captured_stdout, captured_stderr = Code_Exec.run_code(testing_code_str)
            except:
                print("fail")
                continue
            print("Finish writing file to:",outdir)
            print("Succcess ",successed, captured_stdout, captured_stderr)
#################################################################################################################

if __name__ == "__main__":
    main_dir = r"scitexture_output/"
    num_samples = 5
    image_size= 512
    run_command="generate_texture(outdir,sz="+str(image_size)+",num_samples="+str(num_samples)+")"
    run_all(main_dir, script_file="generate.py",new_dir_name="new512",run_command=run_command,num_samples=num_samples)