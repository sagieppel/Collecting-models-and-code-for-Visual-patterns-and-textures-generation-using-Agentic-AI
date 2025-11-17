import os
import tools.MainFunctions as F2
import tools.MainFunctions_3 as F3
import DIARY
import json_pkl
import shutil
import re


#############################################################################################################################3
def generate_generator(benchmark_dir,add_mode=True,number_of_new=10,number_of_code_fix_retry=2,recheck_originality=True):
    # its essential that benchmark_dir will be in relative path (it will later be converted into import)
    data_file = benchmark_dir+"//data.pkl"
    data_file_back = benchmark_dir + "//data_back.pkl"
    if not os.path.exists(benchmark_dir): os.mkdir(benchmark_dir)
    query_dir = "queries_textures_generation//"
    dt={'qr': {}, "messages":[]}
    for fl in os.listdir(query_dir):
        dt['qr'][fl] = open(query_dir + "//" + fl, "r", encoding="utf-8").read()
    ######################################Suggest bencmarks################################################################################


    data_file_loaded=False
    if os.path.isfile(data_file):
        print("\n\n\nLoad file\n\n\n")
        qr=dt['qr']
        dt=json_pkl.read_pkl(data_file)
        dt['qr']=qr
        data_file_loaded=True

#===========================Suggest new idea==================================================================

    if  number_of_new>0 and (add_mode or  not data_file_loaded):
        print("\n\n\nSuggest Texture generations\n\n\n")
        txt=dt['qr']['suggest_benchmarks'].replace("@@@number_of_new@@@",str(number_of_new))
        if data_file_loaded:
            txt+=dt['qr']['add_suggestions']+ "\n Previous suggested methods: ["
            for ky in dt['benchmarks']:
                txt+=str(ky)+","
            txt+"]"

        resp,dt= F3.get_reponse(dt, text=txt, model="o3") # get response from LLM
#-----------------Convert idea to json------------------------------------------------------------------------
        dt['benchmarks_text']=resp
        dt['messages'].append({"role": "user", "content":dt['qr']['suggestions_to_json']})
        benchmark_dic,dt=F3.get_reponse(dt, messages=dt['messages'][-3:],as_json=True, model="o3")
        if add_mode and 'benchmarks' in dt:
            for ky in benchmark_dic:
                if ky not in dt['benchmarks']:
                    dt['benchmarks'][ky]=benchmark_dic[ky]
                    print(benchmark_dic[ky])
                else:
                    print("error ", ky, "already exists")
        else:
           dt['benchmarks']=benchmark_dic
        json_pkl.save_pkl(dt,data_file)
#=================================Generate code===================================================================================================
    for bname in dt['benchmarks']:
        print("benchmark",bname)
        ent=dt['benchmarks'][bname]

        bdesc = ent["description"]
#---------------------if manual checked applied--------------------------------------------------------
        if "checked" in ent: # this mean this entery passed manual inspection
            if  ent['checked'] == 'pass': continue # if checked and passed continue
            if "code" in ent: # else redo code
                ent["old_code"]=ent["code"]
                del ent["code"]
                del ent['checked']
                ent["redo"]=True
#------------------------------------------------------------------------------------------------------------

        if ('code' in ent) and ('code verified' in ent['code'] or 'finished_and_failed' in ent['code']): continue
        if 'full_overlap' in ent: continue
# -------------------------------Recheck idea originality optional recheck the idea is not already in the list-------------------------------------------------------------------------------------------------

        if recheck_originality and (not 'code' in ent) :
            print("Rechecking Checking originaliy")
            benchmark_list = "\n Previous methods:\n ["
            cnt_ex = 0  # count previous benchmar
            for ky in dt['benchmarks']:
                if bname == ky: continue
                if 'code' not in dt['benchmarks'][ky]: continue
                benchmark_list += str(ky) + "," + ky
                cnt_ex += 1
            benchmark_list += "]\n"
            if cnt_ex > 0:
                chek_query = dt['qr']['Check_originality'].replace("**benchmark_name**", bname).replace(
                    "**existing benchmark**", benchmark_list)
                overlap_check, dt = F3.get_reponse(dt, text=chek_query, as_json=True, model="gpt-5")
                ent["overlap"] = overlap_check
                if ("match" in overlap_check) and overlap_check["match"] == "yes":
                    print("Similar benchmarks Exists", ent["overlap"] )
                    ent['full_overlap'] = True
                    json_pkl.save_pkl(dt, data_file)
                    continue
        # ------------------------------------Implement method to code--------------------------------------------------------------------------------------

        code_query=dt['qr']['implement_code'].replace("**benchmark_name**",bname).replace("**becnhmark_description**",bdesc)
        if (not 'code' in ent) or ('Succeed' not in ent['code']):# or ent['code']['Succeed']=='no':
                    print("\n\n\nWrite code for:" + bname + "\n\n\n")
                    for gg in range(10):

                        code_dic, dt = F3.get_reponse(dt, text=code_query, as_json=True, model="gpt-5")
                        if ('code' in code_dic) and  ('Succeed' not in code_dic) and len(code_dic['code'])>100: code_dic['Succeed']="yes"
                        if ('Succeed' not in code_dic):
                      #       code_query+="\n\nIts very important that the output will be in the precise format described aboce\n\n"
                             continue
                        dt['benchmarks'][bname]['code'] = code_dic
                        dt['benchmarks'][bname]['code']['query'] = code_query
                        break
                    json_pkl.save_pkl(dt, data_file)
                    json_pkl.save_pkl(dt, data_file_back)

    #=============================Run Debug and validate code=========================================================


        #try:
        if ent['code']['Succeed']=='no': continue
        # except:
        #     d=3
        #     x=fsfs
        if 'code verified' not in ent['code'] or ent['code']['code verified']==False:
            print("\n\n\nTest and validate  code for:" + bname + "\n\n\n")
            sname = f"{re.sub(r'[^a-zA-Z]', '_', bname)}"
            dt['benchmarks'][bname]['simple name']= sname
            benchdir=benchmark_dir+"//"+sname+"//"
            code_path = benchdir+"generate.py"
            bench_sample_dir = benchdir + "//textures//"
            dt['benchmarks'][bname]['dir']=benchdir
            testing_code_str = (
                        "\nimport importlib\n"+
                        "\nimport " + F2.path_to_import(code_path) + " as generate\n"+
                        #code_path.replace("//",".").replace(".py","").replace("/",".").replace("..",".") + " as generate\n"+
                        "\nimportlib.reload(generate)"
                        "\noutdir = '"+ bench_sample_dir+"'"+
                        dt['qr']["run_line"]
                        #"\ngenerate.generate_benchmark (texture_dir,shape_dir,outdir, num_samples=30)\n"
            )
            for kk in range(number_of_code_fix_retry+100):
                if not os.path.exists(benchmark_dir): os.mkdir(benchdir)
                code = dt['benchmarks'][bname]['code']['code']
            ###    code_generation_talk=dt['messages'][-2:]
                ln=len(dt['messages'])
                code_verified, path, test_dir, code, captured_stdout, messages = (
                F2.run_debug_code(messages =dt['messages'][-2:], code=code,
                                      code_dir=benchdir, functions_and_var={}, codefilename="generate.py",
                                      testing_code=testing_code_str,task_description=bdesc,time_out=12000))
                with open(test_dir+"//Description.txt","w") as fl: fl.write(bdesc) # write benchmark description
                if  "overlap" in ent:
                     json_pkl.save_json(ent["overlap"],test_dir+"//overlap.txt")
                #...........Recheck benchmark results and output.................................................


                if not code_verified:
                    dt['messages']=dt['messages'][:ln]
                    #continue
                    break

                txt="***Original Code Generation task:***\n"+code_query+"\n\n\n"
                txt+="***Generated Code***:\n"+code+"\n\n\n"
                txt+"***Some info on generated images created by running the code***"
                uniform_error=False
                dark_error=False
                for xx,fl in enumerate(os.listdir(bench_sample_dir)):
                    if ".png" in fl:
                        import cv2
                        im=cv2.imread(bench_sample_dir+"//"+fl)
                        txt+="\nImage: "+fl+"  Size: "+str(im.shape[0:2])+" Pixels values range: "+str(im.min())+" to "+str(im.max())
                        if im.min() == im.max():
                                   uniform_error=True
                                   txt += "\n***This image is obviously error as it only have one value:" + str(
                                       im.max()) + " Fix the code to avoid this cases***\n"

                        if im.max()<10:
                                   dark_error=True
                                   txt += "\n***This image is obviously error the image is way to dark, Fix the code to avoid this cases***\n"
                        if xx>6: break
                #    if dark_error or uniform_error:

                txt += "\n\n\n***Your task:***\n"+dt['qr']['check_code']
                if dark_error:
                    txt +="\n\nOne issue you must fix is that at least is in some images the image is way too dark.\n"
                if uniform_error:
                    txt +="\n\nAn issue you must fix is that some of the images are just uniform (the same value for all pixels).\n"

                if kk >= number_of_code_fix_retry and not (uniform_error or dark_error): break
                if kk >= number_of_code_fix_retry+3: break

                verify_query=txt
                print(txt)
                code_dic, dt = F3.get_reponse(dt, text=verify_query, as_json=True, model="gpt-5")
    #            print(dt['benchmarks'][bname]['code']['discussion'])
                if code_dic['corrections']=='yes':# and len(code_dic['code'])>0:
                    print("\\n\n\n****************************************************************************\n\n\nCode correction found:",code_dic)
                    del dt['benchmarks'][bname]['code']
                    dt['benchmarks'][bname]['code'] = code_dic
                    dt['benchmarks'][bname]['code']['Succeed'] = 'yes'
                    dt['benchmarks'][bname]['code']['query'] = code_query
                    dt['benchmarks'][bname]['code']['fixing_query'] = verify_query

                else:
                    break


                #......................................



            dt['benchmarks'][bname]['code']['code verified'] = code_verified
            if not code_verified: dt['benchmarks'][bname]['code']['finished_and_failed']=True
          ###  dt['benchmarks'][bname]['code']['code'] = code
            json_pkl.save_pkl(dt, data_file)
            json_pkl.save_pkl(dt, data_file_back)
            print("\n\n\nAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\n\nFinished benchmark ",bname,"\nverified ",code_verified,"\n\n\nAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\n\n")

    ################################################################################################################################################################

if __name__=="__main__":
        query_dir = "queries_textures_generation//"
        benchmark_dir = "Textures_test/"#_Fast//" # its essential that this will be in relative path
        data_file = benchmark_dir + "//data.pkl"
        # shape_dir = r"/home/deadcrow/Downloads/SHAPES_2D_350k_UNIFIED"#"shapes//"
        # texture_dir = "texture//"
        add_mode = True # if there already data add to it instead of ignore it
        number_of_code_fix_retry = 1  # 3 # number of times to try to fix code before accepting the final results
        recheck_originality=True # double check the idea is not alreadt performed
     #   number_of_new=5 # number of new benchmarks to add
        for kk in range(100):
            if kk==0:
                number_of_new=5 # allow the method to finish existing
            else:
                number_of_new= 2
            generate_generator(benchmark_dir, add_mode=add_mode, number_of_new=number_of_new, number_of_code_fix_retry=number_of_code_fix_retry,
                           recheck_originality=recheck_originality)

